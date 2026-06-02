from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, City, Player
from backend.app.schemas.service_results import BusinessDividendServiceResult, BusinessPurchaseServiceResult
from backend.app.services.ids import to_uuid
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money


BUSINESS_PURCHASE_PRICES = {
    "shop": money("1200.00"),
    "factory": money("3000.00"),
    "private_hostel": money("5000.00"),
}
DIVIDEND_RATE = money("0.10")
MIN_DIVIDEND_AMOUNT = money("25.00")


def get_business_price(business: Business) -> Decimal | None:
    return BUSINESS_PURCHASE_PRICES.get(business.type)


def get_buyable_businesses(db: Session) -> list[Business]:
    return (
        db.query(Business)
        .filter(
            Business.owner_player_id.is_(None),
            Business.type.in_(list(BUSINESS_PURCHASE_PRICES.keys())),
            Business.status == "active",
        )
        .order_by(Business.name)
        .all()
    )


def get_owned_businesses(db: Session, player_id) -> list[Business]:
    return db.query(Business).filter(Business.owner_player_id == player_id).order_by(Business.name).all()


def cheapest_business_price(db: Session) -> Decimal | None:
    prices = [get_business_price(b) for b in get_buyable_businesses(db)]
    valid_prices = [price for price in prices if price is not None]
    return min(valid_prices) if valid_prices else None


def process_business_purchase(db: Session, player_id: str, business_id: str) -> dict:
    player_uuid = to_uuid(player_id)
    business_uuid = to_uuid(business_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return {"success": False, "message": "Бізнес не знайдено"}

    price = get_business_price(business)
    if price is None:
        return {"success": False, "message": "Цей бізнес не продається в MVP."}

    if business.owner_player_id is not None:
        return {"success": False, "message": "Цей бізнес уже має власника."}

    if money(player.balance) < price:
        return {"success": False, "message": f"Недостатньо коштів для купівлі бізнесу! Потрібно: {price:.2f} ₴."}

    city = db.query(City).filter(City.id == player.city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    debit(db, player, "balance", price)
    credit(db, city, "treasury_balance", price)
    business.owner_player_id = player.id

    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="treasury",
        amount=float(price),
        tax=0.0,
        purpose="business_purchase",
    )

    db.commit()
    return BusinessPurchaseServiceResult(
        success=True,
        message=f"Ви придбали бізнес '{business.name}' за {price:.2f} ₴.",
        business={
            "id": str(business.id),
            "name": business.name,
            "type": business.type,
            "cash_balance": float(business.cash_balance),
            "purchase_price": float(price),
        },
        player={
            "balance": float(player.balance),
        },
    ).model_dump()


def process_business_dividend_collection(db: Session, player_id: str, business_id: str) -> dict:
    player_uuid = to_uuid(player_id)
    business_uuid = to_uuid(business_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return {"success": False, "message": "Бізнес не знайдено"}

    if business.owner_player_id != player.id:
        return {"success": False, "message": "Ви не є власником цього бізнесу."}

    dividend = (money(business.cash_balance) * DIVIDEND_RATE).quantize(money("0.01"))
    if dividend < MIN_DIVIDEND_AMOUNT:
        return {"success": False, "message": f"У бізнесу замало вільної каси для дивідендів. Мінімум: {MIN_DIVIDEND_AMOUNT:.2f} ₴."}

    debit(db, business, "cash_balance", dividend)
    credit(db, player, "balance", dividend)

    log_transaction(
        db,
        player.city_id,
        sender_id=business.id,
        sender_type="business",
        receiver_id=player.id,
        receiver_type="player",
        amount=float(dividend),
        tax=0.0,
        purpose="business_dividend",
    )

    db.commit()
    return BusinessDividendServiceResult(
        success=True,
        message=f"Отримано дивіденд {dividend:.2f} ₴ від бізнесу '{business.name}'.",
        business={
            "id": str(business.id),
            "name": business.name,
            "type": business.type,
            "cash_balance": float(business.cash_balance),
        },
        player={
            "balance": float(player.balance),
        },
        dividend=float(dividend),
    ).model_dump()
