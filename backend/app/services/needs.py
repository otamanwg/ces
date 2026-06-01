from sqlalchemy.orm import Session

from backend.app.models import City, Player
from backend.app.services.ids import to_uuid
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money


MEAL_COST = money("25.00")
MEAL_HUNGER_REDUCTION = 35
WORK_HUNGER_INCREASE = 20
SLEEP_HUNGER_INCREASE = 10
DAY_HUNGER_INCREASE = 5
HUNGER_WARNING_THRESHOLD = 70


def clamp_need(value: int) -> int:
    return max(0, min(100, value))


def increase_hunger(player: Player, amount: int) -> None:
    player.hunger = clamp_need((player.hunger or 0) + amount)


def decrease_hunger(player: Player, amount: int) -> None:
    player.hunger = clamp_need((player.hunger or 0) - amount)


def process_meal_purchase(db: Session, player_id: str) -> dict:
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    if (player.hunger or 0) <= 0:
        return {"success": False, "message": "Ви вже ситі. Їжу краще лишити на потім."}

    if money(player.balance) < MEAL_COST:
        return {"success": False, "message": f"Недостатньо коштів на їжу! Потрібно: {MEAL_COST:.2f} ₴."}

    city = db.query(City).filter(City.id == player.city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    hunger_before = player.hunger or 0
    debit(db, player, "balance", MEAL_COST)
    credit(db, city, "treasury_balance", MEAL_COST)
    decrease_hunger(player, MEAL_HUNGER_REDUCTION)
    if hunger_before >= HUNGER_WARNING_THRESHOLD:
        player.mood = min(100, player.mood + 5)

    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="treasury",
        amount=float(MEAL_COST),
        tax=0.0,
        purpose="food",
    )
    db.commit()

    return {
        "success": True,
        "message": f"Ви поїли за {MEAL_COST:.2f} ₴. Голод зменшився.",
        "player": {
            "balance": float(player.balance),
            "hunger": player.hunger,
            "mood": player.mood,
        },
    }
