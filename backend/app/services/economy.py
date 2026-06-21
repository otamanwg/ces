# Бізнес-логіка економічних процесів: Робота, Оренда, Оподаткування та Інфляція
# Файл: backend/app/services/economy.py

from decimal import Decimal

from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from backend.app.models import Business, CityEconomySnapshot, Player
from backend.app.repositories.city import CityRepository
from backend.app.repositories.hostel import HostelRepository
from backend.app.repositories.player import PlayerRepository
from backend.app.schemas.service_results import (
    DayTickServiceResult,
    RentPaymentServiceResult,
    WorkShiftServiceResult,
)
from backend.app.services.buildings import process_daily_building_upkeep
from backend.app.services.daily_business_revenue import process_all_businesses_daily_revenue
from backend.app.services.ids import to_uuid
from backend.app.services.job_queries import get_active_job
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money
from backend.app.services.needs import (
    DAY_HUNGER_INCREASE,
    SLEEP_HUNGER_INCREASE,
    WORK_HUNGER_INCREASE,
    increase_hunger,
)

ACTIVE_MONEY_TARGET_PER_PLAYER = money("3000.00")
TARGET_DAILY_MONEY_GROWTH_RATE = Decimal("0.0300")
MAX_REPORTED_INFLATION_RATE = Decimal("999.99")


def _active_money_supply(db: Session, city_id) -> Decimal:
    players_balance = db.query(func.sum(Player.balance)).filter(Player.city_id == city_id).scalar() or 0
    businesses_balance = (
        db.query(func.sum(Business.cash_balance))
        .filter(
            Business.city_id == city_id,
            Business.owner_player_id.isnot(None),
        )
        .scalar()
        or 0
    )
    return money(players_balance) + money(businesses_balance)


def _capacity_inflation_rate(active_money: Decimal, player_count: int) -> Decimal:
    target_circulation = money(max(1, player_count)) * ACTIVE_MONEY_TARGET_PER_PLAYER
    if active_money <= target_circulation:
        return money("0.00")

    growth = (active_money - target_circulation) / target_circulation
    return money(min(round(growth * 100, 2), MAX_REPORTED_INFLATION_RATE))


def _calculate_money_growth_rate(active_money: Decimal, previous_active_money: Decimal | None) -> Decimal:
    if previous_active_money is None or previous_active_money <= money("0.00"):
        return money("0.0000")
    return money(round((active_money - previous_active_money) / previous_active_money, 4))


def _calculate_snapshot_inflation_rate(active_money: Decimal, previous_active_money: Decimal | None) -> Decimal:
    if previous_active_money is None or previous_active_money <= money("0.00"):
        return money("0.00")

    money_growth_rate = _calculate_money_growth_rate(active_money, previous_active_money)
    excess_growth = max(money("0.00"), money_growth_rate - TARGET_DAILY_MONEY_GROWTH_RATE)
    return money(min(round(excess_growth * 100, 2), MAX_REPORTED_INFLATION_RATE))


def _latest_economy_snapshot(db: Session, city_id) -> CityEconomySnapshot | None:
    return (
        db.query(CityEconomySnapshot)
        .filter(CityEconomySnapshot.city_id == city_id)
        .order_by(desc(CityEconomySnapshot.game_day))
        .first()
    )


def _record_economy_snapshot(
    db: Session,
    city_id,
    game_day: int,
    active_money: Decimal,
    player_count: int,
) -> CityEconomySnapshot:
    previous_snapshot = _latest_economy_snapshot(db, city_id)
    previous_active_money = money(previous_snapshot.active_money_supply) if previous_snapshot is not None else None
    money_growth_rate = _calculate_money_growth_rate(active_money, previous_active_money)
    inflation_rate = (
        _calculate_snapshot_inflation_rate(active_money, previous_active_money)
        if previous_snapshot is not None
        else _capacity_inflation_rate(active_money, player_count)
    )

    snapshot = CityEconomySnapshot(
        city_id=city_id,
        game_day=game_day,
        active_money_supply=active_money,
        previous_active_money_supply=previous_active_money,
        target_growth_rate=TARGET_DAILY_MONEY_GROWTH_RATE,
        money_growth_rate=money_growth_rate,
        inflation_rate=inflation_rate,
    )
    db.add(snapshot)
    return snapshot


def process_shift_work(db: Session, player_id: str) -> dict:
    """Обробка робочої зміни гравця (Виснаження енергії, виплата ЗП, сплата податку в Скарбницю)"""
    player_uuid = to_uuid(player_id)
    player = PlayerRepository(db).get_by_id_for_update(player_uuid)
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    job = get_active_job(db, player_uuid)
    if not job:
        return {
            "success": False,
            "message": "Ви не працевлаштовані. Знайдіть роботу в Центрі Зайнятості.",
        }

    # Перевірка на активний страйк профспілки
    from backend.app.models import LaborUnion

    union = db.query(LaborUnion).filter(LaborUnion.business_id == job.business_id).first()
    if union and union.strike_active:
        return {
            "success": False,
            "message": f"❌ СТРАЙК! Профспілка підприємства '{job.business.name}' оголосила страйк. Робочі зміни заблоковано.",
        }

    # Перевірка ліміту енергії
    if player.energy < job.energy_cost_per_shift:
        return {
            "success": False,
            "message": f"Недостатньо енергії! Необхідно: {job.energy_cost_per_shift}, у вас: {player.energy}. Спочатку відпочиньте.",
        }

    city = CityRepository(db).get_by_id(player.city_id)
    business = db.query(Business).filter(Business.id == job.business_id).first()

    # Розрахунок ЗП
    hours = 8
    gross_salary = money(job.salary_per_hour) * hours

    # Розрахунок податку
    income_tax_rate = money(city.tax_rate_income) / Decimal("100.00")
    tax_amount = gross_salary * income_tax_rate
    net_salary = gross_salary - tax_amount

    # Виконання транзакції
    player.energy -= job.energy_cost_per_shift
    increase_hunger(player, WORK_HUNGER_INCREASE)
    credit(db, player, "balance", net_salary)

    # Зміна балансів казначейства та бізнесу
    credit(db, city, "treasury_balance", tax_amount)

    # Зарплата виплачується з балансу бізнесу (якщо це приватний) або казначейства (державний)
    if business.owner_player_id is None:  # Комунальне/державне підприємство
        debit(db, city, "treasury_balance", gross_salary)
    else:
        debit(db, business, "cash_balance", gross_salary)

    # Логування ЗП
    salary_sender_id = city.id if business.owner_player_id is None else business.id
    salary_sender_type = "treasury" if business.owner_player_id is None else "business"
    log_transaction(
        db,
        city.id,
        sender_id=salary_sender_id,
        sender_type=salary_sender_type,
        receiver_id=player.id,
        receiver_type="player",
        amount=float(net_salary),
        tax=float(tax_amount),
        purpose="salary",
    )

    db.commit()

    return WorkShiftServiceResult(
        success=True,
        message=f"Зміну успішно відпрацьовано! Отримано {net_salary:.2f} ₴ (після податку {city.tax_rate_income}%).",
        player={
            "balance": float(player.balance),
            "energy": player.energy,
            "hunger": player.hunger,
        },
        city={"treasury_balance": float(city.treasury_balance)},
    ).model_dump()


def process_rent_payment(db: Session, player_id: str) -> dict:
    """Нічний сон гравця: одноразова оплата оренди та відновлення енергії/настрою."""
    player_uuid = to_uuid(player_id)
    player = PlayerRepository(db).get_by_id_for_update(player_uuid)
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    hostel = HostelRepository(db).get_by_tenant(player_uuid)
    if not hostel:
        return {
            "success": False,
            "message": "У вас немає орендованого житла. Ви спите на вулиці.",
        }

    city = CityRepository(db).get_by_id(player.city_id)
    business = db.query(Business).filter(Business.id == hostel.business_id).first()

    rent_price = money(hostel.rent_price_per_day)

    # Перевірка наявності коштів
    if money(player.balance) >= rent_price:
        debit(db, player, "balance", rent_price)
        player.energy = min(100, player.energy + (hostel.energy_regen_per_hour * 8))  # 8 годин сну
        player.mood = min(100, player.mood + 15)
        increase_hunger(player, SLEEP_HUNGER_INCREASE)

        # Гроші за оренду йдуть власнику хостелу (приватний бізнес або Скарбниця міста)
        if business.owner_player_id is None:
            credit(db, city, "treasury_balance", rent_price)
        else:
            credit(db, business, "cash_balance", rent_price)

        log_transaction(
            db,
            city.id,
            sender_id=player.id,
            sender_type="player",
            receiver_id=city.id if business.owner_player_id is None else business.id,
            receiver_type="treasury" if business.owner_player_id is None else "business",
            amount=float(rent_price),
            tax=0.0,
            purpose="rent",
        )
        message = f"Сплачено {rent_price:.2f} ₴ за оренду хостелу. Ви чудово виспались!"
    else:
        # Безкоштовний сон на вулиці (погане відновлення)
        player.energy = min(100, player.energy + 20)
        player.mood = max(10, player.mood - 20)
        increase_hunger(player, SLEEP_HUNGER_INCREASE)
        message = "Недостатньо коштів на оренду! Ви спали на лавці в парку. Енергія майже не відновилась."

    db.commit()
    return RentPaymentServiceResult(
        success=True,
        message=message,
        player={
            "balance": float(player.balance),
            "energy": player.energy,
            "mood": player.mood,
            "hunger": player.hunger,
        },
    ).model_dump()


def update_inflation_rate(db: Session, city_id: str) -> float:
    """Автоматичний прорахунок активної грошової маси та інфляції"""
    city_uuid = to_uuid(city_id)
    city = CityRepository(db).get_by_id(city_uuid)
    if not city:
        return 0.0

    active_money = _active_money_supply(db, city_uuid)
    latest_snapshot = _latest_economy_snapshot(db, city_uuid)
    if latest_snapshot is not None:
        previous_active_money = money(latest_snapshot.active_money_supply)
        city.inflation_rate = _calculate_snapshot_inflation_rate(active_money, previous_active_money)
    else:
        num_players = db.query(func.count(Player.id)).filter(Player.city_id == city_uuid).scalar() or 1
        city.inflation_rate = _capacity_inflation_rate(active_money, num_players)

    db.commit()
    return float(city.inflation_rate)


def game_day_tick(db: Session, city_id: str) -> dict:
    """Dev-тick міста: пасивна втома, настрій та інфляція. Оренда — лише через sleep."""
    city_uuid = to_uuid(city_id)
    city = CityRepository(db).get_by_id(city_uuid)
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    # Очищення застарілих записів ідемпотентності (старших за 1 день)
    from backend.app.models import IdempotencyRecord

    db.query(IdempotencyRecord).filter(IdempotencyRecord.created_at < func.now() - text("INTERVAL '1 day'")).delete(
        synchronize_session=False
    )

    active_before = _active_money_supply(db, city_uuid)
    players_updated = 0
    homeless_players = 0
    hungry_players = 0

    players = PlayerRepository(db).list_by_city_with_hostel(city_uuid)
    for player in players:
        players_updated += 1
        player.energy = max(0, player.energy - 5)
        player.mood = max(10, player.mood - 2)
        increase_hunger(player, DAY_HUNGER_INCREASE)
        if player.hunger >= 90:
            hungry_players += 1
            player.mood = max(10, player.mood - 5)

        hostel = player.hostel_rented
        if not hostel:
            homeless_players += 1
            player.mood = max(10, player.mood - 8)

    # Обробка щоденних доходів бізнесу
    business_revenue_stats = process_all_businesses_daily_revenue(db, city_uuid)

    building_upkeep_stats = process_daily_building_upkeep(db, city)
    db.flush()

    active_after = _active_money_supply(db, city_uuid)
    player_count = max(1, len(players))
    next_game_day = (city.game_day or 0) + 1
    snapshot = _record_economy_snapshot(db, city_uuid, next_game_day, active_after, player_count)
    city.inflation_rate = snapshot.inflation_rate
    city.game_day = next_game_day

    # Phase G2: NPC-резиденти — ЗП/премія і цикл витрат для вже найнятих NPC.
    # Генерація NPC — явна (гравець наймає через API), не автоматична в day tick.
    from backend.app.services.npc_service import (
        process_npc_payroll,
        process_npc_spending,
    )

    process_npc_payroll(db, city_uuid, next_game_day)
    process_npc_spending(db, city_uuid, next_game_day)
    db.flush()

    # Phase G3: Комунальні служби — платежі, банкрутство, екстрені контракти.
    from backend.app.services.utility_service import (
        check_utility_bankruptcy,
        process_utility_payments,
    )

    process_utility_payments(db, city_uuid, next_game_day)
    check_utility_bankruptcy(db, city_uuid, next_game_day)
    db.flush()

    # Phase G5: Банк — нарахування відсотків по депозитах і кредитах.
    from backend.app.services.bank_service import process_deposit_interest, process_loan_interest

    process_deposit_interest(db, city_uuid, next_game_day)
    process_loan_interest(db, city_uuid, next_game_day)
    db.flush()

    # Phase G1: динамічні метрики районів + композитні індекси + сезонність.
    # Викликається після NPC-операцій, щоб population включало NPC.
    from backend.app.services.district_metrics import recalculate_all_districts

    recalculate_all_districts(db, city_uuid, next_game_day)
    db.flush()

    db.commit()

    return DayTickServiceResult(
        success=True,
        message="Настав новий день. Оренду сплачуйте кнопкою «Спати».",
        city={
            "id": str(city.id),
            "game_day": city.game_day,
            "inflation_rate": float(city.inflation_rate),
            "treasury_balance": float(city.treasury_balance),
        },
        stats={
            "players_updated": players_updated,
            "rent_collected": 0.0,
            "homeless_players": homeless_players,
            "hungry_players": hungry_players,
            "building_upkeep_charged": building_upkeep_stats["building_upkeep_charged"],
            "buildings_upkeep_charged": building_upkeep_stats["buildings_upkeep_charged"],
            "buildings_upkeep_failed": building_upkeep_stats["buildings_upkeep_failed"],
            "businesses_processed": business_revenue_stats.get("data", {}).get("total_businesses", 0),
            "businesses_successful": business_revenue_stats.get("data", {}).get("successful", 0),
            "businesses_failed": business_revenue_stats.get("data", {}).get("failed", 0),
            "businesses_bankrupted": business_revenue_stats.get("data", {}).get("bankrupted", 0),
            "total_business_revenue": business_revenue_stats.get("data", {}).get("total_revenue", 0.0),
            "total_business_expenses": business_revenue_stats.get("data", {}).get("total_expenses", 0.0),
            "total_business_taxes": business_revenue_stats.get("data", {}).get("total_taxes", 0.0),
            "active_money_before": float(active_before),
            "active_money_after": float(active_after),
            "money_growth_rate": float(snapshot.money_growth_rate),
            "target_growth_rate": float(snapshot.target_growth_rate),
        },
    ).model_dump()
