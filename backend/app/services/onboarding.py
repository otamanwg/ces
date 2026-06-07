from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets

from sqlalchemy.orm import Session

from backend.app.models import Hostel, Player, PlayerOnboarding, PoliceRecord
from backend.app.services.ledger import credit, log_transaction
from backend.app.services.money import money

ARRIVAL_CHOICE = "arrival_choice"
HOUSING_SEARCH = "housing_search"
COMPLETED = "completed"

REPORT_TO_POLICE = "report_to_police"
FIND_HOUSING = "find_housing"

POLICE_NOT_FILED = "not_filed"
POLICE_PENDING = "pending"
POLICE_CLOSED_NO_RECOVERY = "closed_no_recovery"
POLICE_RECOVERED = "recovered"

STARTING_CASH_MIN = 300
STARTING_CASH_MAX = 400
ONBOARDING_REQUIRED_MESSAGE = "Спочатку завершіть прибуття до міста."


def random_starting_cash(rng=None) -> Decimal:
    source = rng or secrets.SystemRandom()
    return money(source.randint(STARTING_CASH_MIN, STARTING_CASH_MAX))


def create_player_onboarding(db: Session, player: Player) -> PlayerOnboarding:
    onboarding = PlayerOnboarding(
        player_id=player.id,
        stage=ARRIVAL_CHOICE,
        police_report_status=POLICE_NOT_FILED,
    )
    db.add(onboarding)
    return onboarding


def get_player_onboarding(db: Session, player: Player) -> PlayerOnboarding | None:
    if player.onboarding is not None:
        return player.onboarding
    return db.query(PlayerOnboarding).filter(PlayerOnboarding.player_id == player.id).first()


def is_onboarding_complete(db: Session, player: Player) -> bool:
    onboarding = get_player_onboarding(db, player)
    return onboarding is None or onboarding.stage == COMPLETED


def is_police_recovery_claimable(
    onboarding: PlayerOnboarding | None,
    *,
    now: datetime | None = None,
) -> bool:
    if (
        onboarding is None
        or onboarding.police_report_status != POLICE_PENDING
        or onboarding.police_recovery_available_at is None
        or money(onboarding.police_recovery_amount or 0) <= Decimal("0.00")
    ):
        return False
    return (now or datetime.now(timezone.utc)) >= onboarding.police_recovery_available_at


def build_onboarding_snapshot(
    db: Session,
    player: Player,
    *,
    now: datetime | None = None,
) -> dict:
    onboarding = get_player_onboarding(db, player)
    if onboarding is None:
        return {
            "stage": COMPLETED,
            "completed": True,
            "title": "Прибуття завершено",
            "narrative": "Ви вже облаштувались у місті.",
            "available_choices": [],
            "police_report_status": POLICE_NOT_FILED,
            "police_recovery_amount": None,
            "police_recovery_available_at": None,
            "police_recovery_claimable": False,
        }

    if onboarding.stage == ARRIVAL_CHOICE:
        title = "Новий початок"
        narrative = (
            "Таксі зникло разом із вашим багажем. У телефоні залишились фото документів, "
            "а в кишені лише стартові гроші. Можна звернутись у поліцію або негайно шукати житло."
        )
        choices = [REPORT_TO_POLICE, FIND_HOUSING]
    elif onboarding.stage == HOUSING_SEARCH:
        title = "Нічліг у новому місті"
        narrative = (
            "Заяву прийнято. Розслідування триватиме окремо, а зараз потрібно знайти місце на ніч "
            "і перейти до самостійного життя у місті."
        )
        choices = [FIND_HOUSING]
    else:
        title = "Прибуття завершено"
        narrative = "Ви знайшли тимчасове житло. Місто відкрите для роботи, навчання і бізнесу."
        choices = []

    return {
        "stage": onboarding.stage,
        "completed": onboarding.stage == COMPLETED,
        "title": title,
        "narrative": narrative,
        "available_choices": choices,
        "police_report_status": onboarding.police_report_status,
        "police_recovery_amount": (
            float(onboarding.police_recovery_amount) if onboarding.police_recovery_amount is not None else None
        ),
        "police_recovery_available_at": (
            onboarding.police_recovery_available_at.isoformat()
            if onboarding.police_recovery_available_at is not None
            else None
        ),
        "police_recovery_claimable": is_police_recovery_claimable(onboarding, now=now),
    }


def choose_onboarding_path(
    db: Session,
    player: Player,
    choice: str,
    *,
    rng=None,
    now: datetime | None = None,
) -> dict:
    onboarding = get_player_onboarding(db, player)
    if onboarding is None or onboarding.stage == COMPLETED:
        return {"success": False, "message": "Прибуття вже завершено."}

    current_time = now or datetime.now(timezone.utc)

    if choice == REPORT_TO_POLICE:
        if onboarding.stage != ARRIVAL_CHOICE:
            return {"success": False, "message": "Заяву до поліції вже подано."}

        source = rng or secrets.SystemRandom()
        recovery_possible = source.random() < 0.55
        if recovery_possible:
            onboarding.police_report_status = POLICE_PENDING
            onboarding.police_recovery_amount = money(source.randint(40, 120))
            onboarding.police_recovery_available_at = current_time + timedelta(hours=source.randint(12, 72))
            recovery_message = "Поліція повідомить, якщо частину майна знайдуть."
        else:
            onboarding.police_report_status = POLICE_CLOSED_NO_RECOVERY
            onboarding.police_recovery_amount = None
            onboarding.police_recovery_available_at = None
            recovery_message = "Швидких зачіпок немає, але заяву зареєстровано."

        onboarding.stage = HOUSING_SEARCH
        db.add(
            PoliceRecord(
                player_id=player.id,
                offense_type="arrival_baggage_theft",
                status="victim_report_filed",
            )
        )
        db.commit()
        db.refresh(onboarding)
        return {
            "success": True,
            "message": f"Заяву про крадіжку прийнято. {recovery_message}",
        }

    if choice == FIND_HOUSING:
        free_room = (
            db.query(Hostel)
            .filter(Hostel.tenant_player_id.is_(None))
            .order_by(Hostel.rent_price_per_day, Hostel.room_number)
            .first()
        )
        if free_room is None:
            return {
                "success": False,
                "message": "Вільного місця на ніч немає. Спробуйте оновити оголошення.",
            }

        free_room.tenant_player_id = player.id
        onboarding.stage = COMPLETED
        onboarding.completed_at = current_time
        db.commit()
        db.refresh(onboarding)
        return {
            "success": True,
            "message": f"Знайдено тимчасове житло: кімната №{free_room.room_number}.",
        }

    return {"success": False, "message": "Невідомий вибір прибуття."}


def claim_police_recovery(
    db: Session,
    player: Player,
    *,
    now: datetime | None = None,
) -> dict:
    onboarding = get_player_onboarding(db, player)
    if onboarding is None or onboarding.police_report_status != POLICE_PENDING:
        return {"success": False, "message": "Немає активного повернення майна від поліції."}

    current_time = now or datetime.now(timezone.utc)
    if onboarding.police_recovery_available_at is None or current_time < onboarding.police_recovery_available_at:
        return {
            "success": False,
            "message": "Розслідування ще триває.",
        }

    amount = money(onboarding.police_recovery_amount or 0)
    if amount <= Decimal("0.00"):
        onboarding.police_report_status = POLICE_CLOSED_NO_RECOVERY
        db.commit()
        return {"success": False, "message": "Справу закрито без повернення коштів."}

    credit(db, player, "balance", amount)
    log_transaction(
        db,
        city_id=str(player.city_id),
        sender_id=str(player.city_id),
        sender_type="system",
        receiver_id=str(player.id),
        receiver_type="player",
        amount=float(amount),
        tax=0,
        purpose="police_recovery",
    )
    onboarding.police_report_status = POLICE_RECOVERED
    db.commit()
    db.refresh(player)
    return {
        "success": True,
        "message": f"Поліція повернула частину втрачених коштів: {amount:.0f} ₴.",
        "amount": float(amount),
    }
