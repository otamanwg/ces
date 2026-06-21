"""
Ательє — створення та продаж скінів (Phase G9).

Механіки:
- Дизайнер створює скін (Skin) через ательє-бізнес.
- Гравець купує скін: платить ціну, отримує PlayerSkin, copies_sold++.
- Комісія ательє (20%) → cash_balance бізнесу; податок (10%) → treasury міста.
- Унікальні скіни мають copies_total=1 і множник ціни x5.
- Екіпірування: лише один скін active одночасно.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, City, Player, PlayerSkin, Skin

logger = logging.getLogger("AtelierService")

# --- Константи ---
RARITY_PRICE_MULTIPLIERS = {
    "common": Decimal("1.0"),
    "rare": Decimal("3.0"),
    "epic": Decimal("10.0"),
    "legendary": Decimal("50.0"),
}
BASE_SKIN_PRICE = Decimal("100.00")
ATELIER_COMMISSION_PCT = Decimal("0.20")  # 20% ательє
SKIN_TAX_PCT = Decimal("0.10")  # 10% податок до treasury
UNIQUE_PRICE_MULTIPLIER = Decimal("5.0")

ALLOWED_RARITIES = set(RARITY_PRICE_MULTIPLIERS.keys())


def calculate_skin_price(rarity: str, is_unique: bool) -> Decimal:
    """Базова ціна * множник рідкості * (5.0 якщо унікальний інакше 1.0)."""
    multiplier = RARITY_PRICE_MULTIPLIERS.get(rarity, Decimal("1.0"))
    unique_mult = UNIQUE_PRICE_MULTIPLIER if is_unique else Decimal("1.0")
    return (BASE_SKIN_PRICE * multiplier * unique_mult).quantize(Decimal("0.01"))


def create_skin(
    db: Session,
    designer: Player,
    atelier_business: Business | None,
    name: str,
    config: dict,
    rarity: str,
    is_unique: bool,
    copies_total: int,
    price: Decimal | None = None,
) -> dict:
    """Дизайнер створює скін через ательє.

    Якщо is_unique — copies_total примусово = 1.
    Якщо price не задано — обчислюється через calculate_skin_price.
    """
    if rarity not in ALLOWED_RARITIES:
        return {
            "success": False,
            "message": f"Невідома рідкість '{rarity}'. Доступні: {sorted(ALLOWED_RARITIES)}.",
        }

    if not name or not name.strip():
        return {"success": False, "message": "Назва скіну не може бути порожньою."}

    if not isinstance(config, dict):
        return {"success": False, "message": "config має бути словником."}

    if is_unique:
        copies_total = 1
    else:
        if copies_total < 1:
            return {"success": False, "message": "copies_total має бути >= 1."}

    final_price = Decimal(str(price)) if price is not None else calculate_skin_price(rarity, is_unique)
    if final_price < 0:
        return {"success": False, "message": "Ціна не може бути від'ємною."}

    atelier_id = atelier_business.id if atelier_business is not None else None

    skin = Skin(
        designer_id=designer.id,
        atelier_id=atelier_id,
        name=name.strip(),
        config=config,
        rarity=rarity,
        is_unique=is_unique,
        copies_total=copies_total,
        copies_sold=0,
        price=final_price,
        created_at=datetime.now(UTC),
    )
    db.add(skin)
    db.flush()
    logger.info(
        "Скін створено: designer=%s name='%s' rarity=%s unique=%s price=%s copies=%d",
        designer.username,
        name,
        rarity,
        is_unique,
        final_price,
        copies_total,
    )
    return {
        "success": True,
        "message": "Скін успішно створено.",
        "skin_id": str(skin.id),
    }


def buy_skin(
    db: Session,
    buyer: Player,
    skin: Skin,
    atelier_business: Business | None = None,
) -> dict:
    """Гравець купує скін.

    - З balance гравця списується price.
    - Створюється PlayerSkin (унікальне по (player_id, skin_id)).
    - copies_sold++. Якщо copies_sold >= copies_total → sold out.
    - Комісія 20% → cash_balance ательє; податок 10% → treasury міста.
    """
    # Перевірка наявності
    if skin.copies_sold >= skin.copies_total:
        return {"success": False, "message": "Скін розпродано (sold out)."}

    price = Decimal(str(skin.price))
    if Decimal(str(buyer.balance)) < price:
        return {"success": False, "message": "Недостатньо коштів для покупки скіну."}

    # Перевірка що гравець ще не має цього скіну
    existing = (
        db.query(PlayerSkin)
        .filter(
            PlayerSkin.player_id == buyer.id,
            PlayerSkin.skin_id == skin.id,
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Ви вже володієте цим скіном."}

    # Розподіл коштів
    commission = (price * ATELIER_COMMISSION_PCT).quantize(Decimal("0.01"))
    tax = (price * SKIN_TAX_PCT).quantize(Decimal("0.01"))
    designer_proceeds = (price - commission - tax).quantize(Decimal("0.01"))

    # Списання з покупця
    buyer.balance = Decimal(str(buyer.balance)) - price

    # Комісія ательє
    atelier = atelier_business
    if atelier is None and skin.atelier_id is not None:
        atelier = db.query(Business).filter(Business.id == skin.atelier_id).first()
    if atelier is not None:
        atelier.cash_balance = Decimal(str(atelier.cash_balance)) + commission

    # Податок до treasury міста
    city = db.query(City).filter(City.id == buyer.city_id).first()
    if city is not None:
        city.treasury_balance = Decimal(str(city.treasury_balance)) + tax

    # Дизайнеру — решта (зарахуємо на balance дизайнера)
    designer = db.query(Player).filter(Player.id == skin.designer_id).first()
    if designer is not None:
        designer.balance = Decimal(str(designer.balance)) + designer_proceeds

    # PlayerSkin
    player_skin = PlayerSkin(
        player_id=buyer.id,
        skin_id=skin.id,
        is_equipped=False,
        acquired_at=datetime.now(UTC),
    )
    db.add(player_skin)

    skin.copies_sold = skin.copies_sold + 1
    db.flush()

    sold_out = skin.copies_sold >= skin.copies_total
    logger.info(
        "Скін куплено: buyer=%s skin='%s' price=%s commission=%s tax=%s designer_proceeds=%s sold_out=%s",
        buyer.username,
        skin.name,
        price,
        commission,
        tax,
        designer_proceeds,
        sold_out,
    )
    return {
        "success": True,
        "message": "Скін успішно куплено." + (" Скін розпродано." if sold_out else ""),
        "player_skin_id": str(player_skin.id),
    }


def equip_skin(db: Session, player: Player, player_skin: PlayerSkin) -> dict:
    """Екіпірувати скін: зняти всі інші, надіти цей."""
    if player_skin.player_id != player.id:
        return {"success": False, "message": "Цей скін не належить вам."}

    # Зняти всі інші
    db.query(PlayerSkin).filter(
        PlayerSkin.player_id == player.id,
        PlayerSkin.is_equipped.is_(True),
    ).update({PlayerSkin.is_equipped: False}, synchronize_session=False)

    player_skin.is_equipped = True
    db.flush()
    logger.info("Скін екіпіровано: player=%s player_skin=%s", player.username, player_skin.id)
    return {"success": True, "message": "Скін екіпіровано."}


def unequip_all(db: Session, player: Player) -> dict:
    """Зняти всі скіни гравця."""
    updated = (
        db.query(PlayerSkin)
        .filter(
            PlayerSkin.player_id == player.id,
            PlayerSkin.is_equipped.is_(True),
        )
        .update({PlayerSkin.is_equipped: False}, synchronize_session=False)
    )
    db.flush()
    logger.info("Усі скіни знято: player=%s count=%d", player.username, updated)
    return {"success": True, "message": "Усі скіни знято.", "unequipped_count": int(updated)}


def list_skins_for_sale(db: Session, atelier_business: Business) -> list[dict]:
    """Скіни в продажу у заданому ательє (copies_sold < copies_total)."""
    skins = (
        db.query(Skin)
        .filter(
            Skin.atelier_id == atelier_business.id,
            Skin.copies_sold < Skin.copies_total,
        )
        .order_by(Skin.created_at.desc())
        .all()
    )
    return [
        {
            "skin_id": str(s.id),
            "name": s.name,
            "rarity": s.rarity,
            "is_unique": s.is_unique,
            "price": float(s.price),
            "copies_total": s.copies_total,
            "copies_sold": s.copies_sold,
            "copies_available": s.copies_total - s.copies_sold,
            "designer_id": str(s.designer_id),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in skins
    ]


def list_player_skins(db: Session, player: Player) -> list[dict]:
    """Скіни гравця зі статусом екіпіровки."""
    rows = (
        db.query(PlayerSkin, Skin)
        .join(Skin, PlayerSkin.skin_id == Skin.id)
        .filter(PlayerSkin.player_id == player.id)
        .order_by(PlayerSkin.acquired_at.desc())
        .all()
    )
    return [
        {
            "player_skin_id": str(ps.id),
            "skin_id": str(s.id),
            "name": s.name,
            "rarity": s.rarity,
            "is_unique": s.is_unique,
            "is_equipped": ps.is_equipped,
            "acquired_at": ps.acquired_at.isoformat() if ps.acquired_at else None,
        }
        for ps, s in rows
    ]
