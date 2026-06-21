"""
Тіньова економіка (Phase G9).

Механіки:
- criminal_rep — кримінальна репутація гравця (0-100), росте від тіньових операцій.
- ShadowBusiness — тіньові бізнеси (illegal_casino, smuggling, shadow_pharmacy, illegal_bar, money_laundering).
- Щоденний дохід від тіньового бізнесу, шанс викриття залежить від criminal_rep.
- Тіньовий ринок: купівля/продаж контрабанди без податків.
- Відмивання грошей: комісія 15%, +5 criminal_rep обом сторонам.
- Шахрайські пропозиції: шанс залежить від criminal_rep.
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import (
    CorruptionLog,
    CriminalRepLog,
    Player,
    ShadowBusiness,
)

logger = logging.getLogger("ShadowService")

# --- Константи ---
SHADOW_BUSINESS_UNLOCK_REP = 30
CRIMINAL_REP_MAX = 100
CRIMINAL_REP_DECAY_MONTHLY = 1.0
SHADOW_TYPES = (
    "illegal_casino",
    "smuggling",
    "shadow_pharmacy",
    "illegal_bar",
    "money_laundering",
)
DISCOVERY_BASE_CHANCE = 0.05
DISCOVERY_CHANCE_PER_REP = 0.003

# Діапазони щоденного доходу за типом тіньового бізнесу
SHADOW_INCOME_RANGES = {
    "illegal_casino": (50, 200),
    "smuggling": (100, 500),
    "shadow_pharmacy": (80, 300),
    "illegal_bar": (30, 100),
    "money_laundering": (200, 1000),
}

# Базові "легальні" ціни для оцінки контрабанди (спрощено)
_LEGAL_PRICE_REFERENCE = {
    "alcohol": Decimal("100.00"),
    "tobacco": Decimal("80.00"),
    "medicine": Decimal("150.00"),
    "weapons": Decimal("1000.00"),
    "electronics": Decimal("300.00"),
}
DEFAULT_LEGAL_PRICE = Decimal("100.00")

# Комісія відмивача
LAUNDERING_COMMISSION_RATE = Decimal("0.15")
LAUNDERING_REP_GAIN = 5.0

# Шахрайство
FRAUD_REP_GAIN_MIN = 5.0
FRAUD_REP_GAIN_MAX = 10.0
FRAUD_MONEY_MIN = Decimal("500.00")
FRAUD_MONEY_MAX = Decimal("5000.00")
REFUSE_FRAUD_REP_GAIN = 1.0

# Тіньовий ринок
SHADOW_BUY_DISCOUNT = Decimal("0.60")  # 60% легальної ціни
SHADOW_SELL_RATE = Decimal("0.80")  # 80% легальної ціни (без податку)
SHADOW_MARKET_REP_GAIN = 2.0


def _now() -> datetime:
    return datetime.now(UTC)


def _clamp_rep(rep: float) -> float:
    if rep < 0:
        return 0.0
    if rep > CRIMINAL_REP_MAX:
        return float(CRIMINAL_REP_MAX)
    return float(rep)


# --- criminal_rep ---


def add_criminal_rep(db: Session, player: Player, delta: float, reason: str) -> dict:
    """Змінює criminal_rep гравця з записом у CriminalRepLog.

    Значення обмежується діапазоном 0-100.
    """
    if not reason:
        return {"success": False, "message": "Причина зміни репутації обов'язкова."}

    old_rep = float(player.criminal_rep or 0.0)
    new_rep = _clamp_rep(old_rep + float(delta))
    actual_delta = new_rep - old_rep

    player.criminal_rep = new_rep

    log = CriminalRepLog(
        player_id=player.id,
        delta=actual_delta,
        reason=reason[:40],
    )
    db.add(log)
    db.flush()
    logger.info(
        "criminal_rep змінено: гравець=%s delta=%s new_rep=%s reason=%s",
        player.username,
        actual_delta,
        new_rep,
        reason,
    )
    return {"success": True, "message": "Кримінальну репутацію оновлено.", "new_rep": new_rep}


def decay_criminal_rep(db: Session, player: Player) -> dict:
    """Щомісячне зниження criminal_rep за чесну поведінку (викликається на day tick).

    Зменшує на CRIMINAL_REP_DECAY_MONTHLY, не нижче 0.
    """
    old_rep = float(player.criminal_rep or 0.0)
    if old_rep <= 0:
        return {"success": True, "new_rep": 0.0}

    new_rep = _clamp_rep(old_rep - CRIMINAL_REP_DECAY_MONTHLY)
    actual_delta = new_rep - old_rep

    player.criminal_rep = new_rep
    log = CriminalRepLog(
        player_id=player.id,
        delta=actual_delta,
        reason="monthly_decay",
    )
    db.add(log)
    db.flush()
    logger.info("criminal_rep decay: гравець=%s new_rep=%s", player.username, new_rep)
    return {"success": True, "new_rep": new_rep}


def can_access_shadow_market(player: Player) -> bool:
    """Чи має гравець доступ до тіньового ринку (criminal_rep >= 30)."""
    return float(player.criminal_rep or 0.0) >= SHADOW_BUSINESS_UNLOCK_REP


# --- Shadow business ---


def open_shadow_business(db: Session, player: Player, district, business_type: str) -> dict:
    """Відкриває тіньовий бізнес у вказаному районі.

    Вимагає criminal_rep >= SHADOW_BUSINESS_UNLOCK_REP.
    """
    if float(player.criminal_rep or 0.0) < SHADOW_BUSINESS_UNLOCK_REP:
        return {
            "success": False,
            "message": f"Потрібна кримінальна репутація >= {SHADOW_BUSINESS_UNLOCK_REP}.",
        }

    if business_type not in SHADOW_TYPES:
        return {
            "success": False,
            "message": f"Невідомий тип тіньового бізнесу: {business_type}.",
        }

    business = ShadowBusiness(
        owner_id=player.id,
        type=business_type,
        district_id=district.id,
        cash_balance=Decimal("0.00"),
        is_discovered=False,
        discovered_at=None,
    )
    db.add(business)
    db.flush()
    logger.info(
        "Тіньовий бізнес створено: власник=%s тип=%s район=%s",
        player.username,
        business_type,
        getattr(district, "id", None),
    )
    return {
        "success": True,
        "message": "Тіньовий бізнес відкрито.",
        "business_id": str(business.id),
    }


def shadow_business_income(db: Session, shadow_business: ShadowBusiness, game_day: int) -> dict:
    """Нараховує щоденний дохід тіньового бізнесу на основі типу.

    Додає до cash_balance бізнесу.
    """
    if shadow_business.is_discovered:
        return {"success": False, "income": 0.0}

    low, high = SHADOW_INCOME_RANGES.get(shadow_business.type, (0, 0))
    if low == 0 and high == 0:
        return {"success": False, "income": 0.0}

    income = Decimal(str(random.randint(low, high)))
    shadow_business.cash_balance = Decimal(str(shadow_business.cash_balance)) + income
    db.flush()
    logger.info(
        "Тіньовий дохід: бізнес=%s тип=%s день=%s дохід=%s",
        shadow_business.id,
        shadow_business.type,
        game_day,
        income,
    )
    return {"success": True, "income": float(income)}


def check_discovery(db: Session, shadow_business: ShadowBusiness, player: Player) -> dict:
    """Перевіряє, чи викрито тіньовий бізнес.

    Шанс = DISCOVERY_BASE_CHANCE + player.criminal_rep * DISCOVERY_CHANCE_PER_REP.
    При викритті: is_discovered=True, discovered_at=now, створюється CorruptionLog.
    """
    if shadow_business.is_discovered:
        return {"success": True, "discovered": True, "evidence_strength": 0.7}

    rep = float(player.criminal_rep or 0.0)
    chance = DISCOVERY_BASE_CHANCE + rep * DISCOVERY_CHANCE_PER_REP
    if random.random() < chance:
        evidence_strength = 0.7
        shadow_business.is_discovered = True
        shadow_business.discovered_at = _now()

        corruption = CorruptionLog(
            incident_type="shadow_business",
            perpetrator_id=player.id,
            victim_id=None,
            amount=Decimal(str(shadow_business.cash_balance)),
            district_id=shadow_business.district_id,
            evidence_strength=evidence_strength,
            is_reported=False,
            is_investigated=False,
            is_proven=False,
            discovered_at=shadow_business.discovered_at,
        )
        db.add(corruption)
        db.flush()
        logger.info(
            "Тіньовий бізнес викрито: бізнес=%s власник=%s evidence=%s",
            shadow_business.id,
            player.username,
            evidence_strength,
        )
        return {"success": True, "discovered": True, "evidence_strength": evidence_strength}

    return {"success": True, "discovered": False, "evidence_strength": 0.0}


# --- Шахрайство ---


def _fraud_chance(rep: float) -> float:
    if rep < 10:
        return 0.0
    if rep < 30:
        return 0.05
    if rep < 60:
        return 0.15
    return 0.30


def offer_fraud(db: Session, player: Player, game_day: int) -> dict:
    """Пропонує шахрайську можливість залежно від criminal_rep.

    Шанс: <10: 0%, 10-30: 5%, 30-60: 15%, 60-100: 30%.
    """
    rep = float(player.criminal_rep or 0.0)
    chance = _fraud_chance(rep)
    if random.random() >= chance:
        return {"success": True, "offered": False, "description": ""}

    descriptions = [
        "Підробка документів для отримання міської субсидії.",
        "Незаконна схема повернення ПДВ через фіктивні контракти.",
        "Хабар чиновнику за прискорення дозволів на будівництво.",
        "Відмивання готівки через фіктивні консультації.",
    ]
    description = random.choice(descriptions)
    logger.info("Шахрайську пропозицію надано: гравець=%s день=%s", player.username, game_day)
    return {"success": True, "offered": True, "description": description}


def accept_fraud(db: Session, player: Player, amount: Decimal, game_day: int) -> dict:
    """Гравець приймає шахрайську схему: отримує гроші та +5-10 criminal_rep."""
    if amount <= 0:
        amount = Decimal(str(random.randint(int(FRAUD_MONEY_MIN), int(FRAUD_MONEY_MAX))))

    rep_gain = random.uniform(FRAUD_REP_GAIN_MIN, FRAUD_REP_GAIN_MAX)
    player.balance = Decimal(str(player.balance)) + amount
    db.flush()

    rep_result = add_criminal_rep(db, player, rep_gain, "fraud_accepted")
    new_rep = rep_result.get("new_rep", float(player.criminal_rep))

    logger.info(
        "Шахрайство прийнято: гравець=%s день=%s дохід=%s rep_gain=%s",
        player.username,
        game_day,
        amount,
        rep_gain,
    )
    return {
        "success": True,
        "message": "Шахрайську схему реалізовано.",
        "gain": float(amount),
        "rep_gain": rep_gain,
        "new_rep": new_rep,
    }


def refuse_fraud(db: Session, player: Player) -> dict:
    """Гравець відмовляється від шахрайства: +1 репутація за чесну поведінку."""
    rep_result = add_criminal_rep(db, player, -REFUSE_FRAUD_REP_GAIN, "fraud_refused")
    # Відмова = чесна поведінка, тому знижуємо criminal_rep
    logger.info("Шахрайство відхилено: гравець=%s", player.username)
    return {
        "success": True,
        "message": "Ви відмовилися від шахрайства. Чесна поведінка.",
        "new_rep": rep_result.get("new_rep", float(player.criminal_rep)),
    }


# --- Відмивання грошей ---


def money_laundering_service(db: Session, launderer: Player, client: Player, amount: Decimal) -> dict:
    """Відмивання грошей: відмивач бере 15% комісії, клієнт отримує решту.

    +5 criminal_rep обом сторонам.
    """
    if amount <= 0:
        return {"success": False, "message": "Сума має бути додатною."}

    if Decimal(str(client.balance)) < amount:
        return {"success": False, "message": "У клієнта недостатньо коштів."}

    commission = (Decimal(str(amount)) * LAUNDERING_COMMISSION_RATE).quantize(Decimal("0.01"))
    clean_amount = Decimal(str(amount)) - commission

    client.balance = Decimal(str(client.balance)) - amount + clean_amount
    launderer.balance = Decimal(str(launderer.balance)) + commission
    db.flush()

    add_criminal_rep(db, launderer, LAUNDERING_REP_GAIN, "laundering_service")
    add_criminal_rep(db, client, LAUNDERING_REP_GAIN, "laundering_client")

    logger.info(
        "Відмивання: відмивач=%s клієнт=%s сума=%s комісія=%s",
        launderer.username,
        client.username,
        amount,
        commission,
    )
    return {
        "success": True,
        "message": "Гроші відмито.",
        "commission": float(commission),
        "clean_amount": float(clean_amount),
    }


# --- Тіньовий ринок ---


def _legal_price(item_type: str) -> Decimal:
    return _LEGAL_PRICE_REFERENCE.get(item_type, DEFAULT_LEGAL_PRICE)


def shadow_market_buy(db: Session, buyer: Player, item_type: str, quantity: int) -> dict:
    """Купівля контрабанди на тіньовому ринку за 60% легальної ціни. +2 criminal_rep."""
    if not can_access_shadow_market(buyer):
        return {
            "success": False,
            "message": f"Потрібна кримінальна репутація >= {SHADOW_BUSINESS_UNLOCK_REP}.",
        }
    if quantity <= 0:
        return {"success": False, "message": "Кількість має бути додатною."}

    unit_price = (_legal_price(item_type) * SHADOW_BUY_DISCOUNT).quantize(Decimal("0.01"))
    total_cost = (unit_price * Decimal(str(quantity))).quantize(Decimal("0.01"))

    if Decimal(str(buyer.balance)) < total_cost:
        return {"success": False, "message": "Недостатньо коштів."}

    buyer.balance = Decimal(str(buyer.balance)) - total_cost
    db.flush()

    add_criminal_rep(db, buyer, SHADOW_MARKET_REP_GAIN, "shadow_market_buy")

    logger.info(
        "Тіньова купівля: покупець=%s товар=%s кількість=%s вартість=%s",
        buyer.username,
        item_type,
        quantity,
        total_cost,
    )
    return {
        "success": True,
        "message": "Контрабанду куплено на тіньовому ринку.",
        "total_cost": float(total_cost),
        "unit_price": float(unit_price),
    }


def shadow_market_sell(db: Session, seller: Player, item_type: str, quantity: int) -> dict:
    """Продаж контрабанди на тіньовому ринку за 80% легальної ціни (без податку). +2 criminal_rep."""
    if not can_access_shadow_market(seller):
        return {
            "success": False,
            "message": f"Потрібна кримінальна репутація >= {SHADOW_BUSINESS_UNLOCK_REP}.",
        }
    if quantity <= 0:
        return {"success": False, "message": "Кількість має бути додатною."}

    unit_price = (_legal_price(item_type) * SHADOW_SELL_RATE).quantize(Decimal("0.01"))
    total_revenue = (unit_price * Decimal(str(quantity))).quantize(Decimal("0.01"))

    seller.balance = Decimal(str(seller.balance)) + total_revenue
    db.flush()

    add_criminal_rep(db, seller, SHADOW_MARKET_REP_GAIN, "shadow_market_sell")

    logger.info(
        "Тіньовий продаж: продавець=%s товар=%s кількість=%s дохід=%s",
        seller.username,
        item_type,
        quantity,
        total_revenue,
    )
    return {
        "success": True,
        "message": "Контрабанду продано на тіньовому ринку.",
        "total_revenue": float(total_revenue),
        "unit_price": float(unit_price),
    }
