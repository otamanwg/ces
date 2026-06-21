import os
from decimal import Decimal

import pytest

from backend.app.models import (
    Building,
    BuildingApplication,
    Business,
    BusinessBlueprint,
    City,
    CityEconomySnapshot,
    Hostel,
    Job,
    LandParcel,
    Player,
    TransactionModelLog,
)
from backend.app.schemas.service_results import (
    DayTickServiceResult,
    MealPurchaseServiceResult,
    RentPaymentServiceResult,
    WorkShiftServiceResult,
)
from backend.app.seed import seed_initial_data
from backend.app.services.buildings import ACTIVE, BUILDING_UPKEEP_PURPOSE, BUILT
from backend.app.services.economy import (
    ACTIVE_MONEY_TARGET_PER_PLAYER,
    game_day_tick,
    process_rent_payment,
    process_shift_work,
)
from backend.app.services.needs import HUNGER_WARNING_THRESHOLD, MEAL_COST, process_meal_purchase
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

SIMULATION_DAYS = 30
MIN_ACTIVE_MONEY_RATIO = Decimal("0.50")
MAX_ACTIVE_MONEY_RATIO = Decimal("2.00")
MAX_ACCEPTABLE_INFLATION_RATE = Decimal("100.00")
ESSENTIAL_DAILY_COST = Decimal("15.00") + MEAL_COST
MIN_PLAYER_RUNWAY_DAYS = 7
TARGET_DAILY_MONEY_GROWTH_RATE = Decimal("0.0300")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _decimal(value) -> Decimal:
    return Decimal(str(value))


def _create_active_station_kiosk(db, city: City, owner: Player) -> tuple[BusinessBlueprint, Business, Building]:
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "station_kiosk").one()
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    parcel.owner_player_id = owner.id
    parcel.status = BUILT

    metrics = blueprint.metric_effects
    application = BuildingApplication(
        city_id=city.id,
        district_id=parcel.district_id,
        land_parcel_id=parcel.id,
        business_blueprint_id=blueprint.id,
        applicant_player_id=owner.id,
        proposed_name=blueprint.name,
        project_type=blueprint.project_type,
        land_area_hectares=parcel.area_hectares,
        expected_jobs=metrics["expected_jobs"],
        traffic_load=metrics["traffic_load"],
        service_load=metrics["service_load"],
        medical_load=metrics["medical_load"],
        public_benefit=metrics["public_benefit"],
        status="activated",
        mayor_score=100,
        mayor_summary="Deterministic economy validation fixture.",
        mayor_issues=[],
        mayor_questions=[],
    )
    db.add(application)
    db.flush()

    business = Business(
        city_id=city.id,
        name=blueprint.name,
        type=blueprint.business_type,
        owner_player_id=owner.id,
        owner_share_pct=Decimal("100.00"),
        cash_balance=blueprint.recommended_cash_reserve,
        status="active",
        management_mode="ai",
        business_size=1,
    )
    db.add(business)
    db.flush()

    building = Building(
        city_id=city.id,
        district_id=parcel.district_id,
        land_parcel_id=parcel.id,
        source_application_id=application.id,
        business_blueprint_id=blueprint.id,
        business_id=business.id,
        owner_player_id=owner.id,
        name=blueprint.name,
        project_type=blueprint.project_type,
        status=BUILT,
        operating_status=ACTIVE,
    )
    db.add(building)
    db.commit()
    return blueprint, business, building


def test_seeded_production_loop_stays_balanced_for_30_days():
    assert TEST_DATABASE_URL is not None
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).one()
        player = Player(
            city_id=city.id,
            username="economy-30-day-gate",
            balance=Decimal("450.00"),
            energy=100,
            mood=100,
            hunger=0,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).order_by(Hostel.room_number).first()
        job = db.query(Job).filter(Job.min_education == "High School").order_by(Job.salary_per_hour, Job.title).first()
        assert room is not None
        assert job is not None
        room.tenant_player_id = player.id
        job.filled_by_player_id = player.id
        db.commit()

        blueprint, business, building = _create_active_station_kiosk(db, city, player)
        initial_player_cash = _decimal(player.balance)
        initial_business_cash = _decimal(business.cash_balance)
        initial_treasury = _decimal(city.treasury_balance)
        initial_active_money = initial_player_cash + initial_business_cash
        target_active_money = ACTIVE_MONEY_TARGET_PER_PLAYER
        assert initial_active_money < target_active_money

        peak_active_money = initial_active_money
        peak_inflation = Decimal("0.00")
        meals_purchased = 0

        for day in range(1, SIMULATION_DAYS + 1):
            tick_result = game_day_tick(db, str(city.id))
            assert tick_result["success"] is True, f"day {day}: game_day_tick failed"
            DayTickServiceResult.model_validate(tick_result)

            tick_stats = tick_result["stats"]
            assert tick_stats["businesses_processed"] == 1, f"day {day}: production was not processed"
            assert tick_stats["businesses_successful"] == 1, f"day {day}: production failed"
            assert tick_stats["businesses_bankrupted"] == 0, f"day {day}: business bankrupted"
            assert tick_stats["buildings_upkeep_charged"] == 1, f"day {day}: upkeep was not charged"
            assert tick_stats["buildings_upkeep_failed"] == 0, f"day {day}: upkeep failed"
            assert _decimal(tick_stats["active_money_after"]) >= Decimal("0.00")

            work_result = process_shift_work(db, str(player.id))
            assert work_result["success"] is True, f"day {day}: work shift failed"
            WorkShiftServiceResult.model_validate(work_result)

            db.refresh(player)
            if player.hunger >= HUNGER_WARNING_THRESHOLD:
                meal_result = process_meal_purchase(db, str(player.id))
                assert meal_result["success"] is True, f"day {day}: meal purchase failed"
                MealPurchaseServiceResult.model_validate(meal_result)
                meals_purchased += 1

            rent_result = process_rent_payment(db, str(player.id))
            assert rent_result["success"] is True, f"day {day}: sleep/rent failed"
            RentPaymentServiceResult.model_validate(rent_result)

            db.refresh(player)
            db.refresh(business)
            db.refresh(building)
            db.refresh(city)

            current_active_money = _decimal(player.balance) + _decimal(business.cash_balance)
            peak_active_money = max(peak_active_money, current_active_money)
            peak_inflation = max(peak_inflation, _decimal(city.inflation_rate))

            assert _decimal(player.balance) >= Decimal("0.00"), f"day {day}: player cash became negative"
            assert _decimal(business.cash_balance) >= Decimal("0.00"), f"day {day}: business cash became negative"
            assert _decimal(city.treasury_balance) >= Decimal("0.00"), f"day {day}: treasury became negative"
            assert 0 <= player.energy <= 100, f"day {day}: energy escaped bounds"
            assert 0 <= player.hunger <= 100, f"day {day}: hunger escaped bounds"
            assert 10 <= player.mood <= 100, f"day {day}: mood escaped bounds"
            assert business.status == "active", f"day {day}: business stopped operating"
            assert building.operating_status == ACTIVE, f"day {day}: building entered maintenance_due"

        db.refresh(player)
        db.refresh(business)
        db.refresh(city)

        final_player_cash = _decimal(player.balance)
        final_business_cash = _decimal(business.cash_balance)
        final_treasury = _decimal(city.treasury_balance)
        final_active_money = final_player_cash + final_business_cash
        active_money_ratio = final_active_money / target_active_money
        business_operating_gain = final_business_cash - initial_business_cash

        salary_count = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "salary").count()
        rent_count = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "rent").count()
        food_count = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "food").count()
        upkeep_count = (
            db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_UPKEEP_PURPOSE).count()
        )
        economy_snapshots = (
            db.query(CityEconomySnapshot)
            .filter(CityEconomySnapshot.city_id == city.id)
            .order_by(CityEconomySnapshot.game_day)
            .all()
        )

        assert city.game_day == 1 + SIMULATION_DAYS
        assert salary_count == SIMULATION_DAYS
        assert rent_count == SIMULATION_DAYS
        assert upkeep_count == SIMULATION_DAYS
        assert food_count == meals_purchased
        assert meals_purchased >= SIMULATION_DAYS // 2
        assert len(economy_snapshots) == SIMULATION_DAYS
        assert [snapshot.game_day for snapshot in economy_snapshots] == list(range(2, 2 + SIMULATION_DAYS))
        assert economy_snapshots[0].previous_active_money_supply is None
        assert all(
            _decimal(snapshot.target_growth_rate) == TARGET_DAILY_MONEY_GROWTH_RATE for snapshot in economy_snapshots
        )
        for previous_snapshot, current_snapshot in zip(economy_snapshots[:-1], economy_snapshots[1:], strict=True):
            assert _decimal(current_snapshot.previous_active_money_supply) == _decimal(
                previous_snapshot.active_money_supply
            )
            expected_growth = (
                _decimal(current_snapshot.active_money_supply) - _decimal(previous_snapshot.active_money_supply)
            ) / _decimal(previous_snapshot.active_money_supply)
            expected_growth = Decimal(str(round(expected_growth, 4)))
            assert _decimal(current_snapshot.money_growth_rate) == expected_growth
            expected_inflation = max(Decimal("0.00"), expected_growth - TARGET_DAILY_MONEY_GROWTH_RATE) * 100
            expected_inflation = Decimal(str(round(expected_inflation, 2)))
            assert _decimal(current_snapshot.inflation_rate) == expected_inflation

        diagnostics = {
            "days": SIMULATION_DAYS,
            "meals": meals_purchased,
            "initial_active_money": float(initial_active_money),
            "final_active_money": float(final_active_money),
            "active_money_ratio": float(active_money_ratio),
            "peak_active_money": float(peak_active_money),
            "final_inflation_rate": float(_decimal(city.inflation_rate)),
            "peak_inflation_rate": float(peak_inflation),
            "player_cash_change": float(final_player_cash - initial_player_cash),
            "business_cash_change": float(business_operating_gain),
            "treasury_cash_change": float(final_treasury - initial_treasury),
        }

        acceptance_checks = {
            "active money retained at least 50% of the monthly per-player target": (
                active_money_ratio >= MIN_ACTIVE_MONEY_RATIO
            ),
            "active money did not exceed twice the monthly per-player target": (
                active_money_ratio <= MAX_ACTIVE_MONEY_RATIO
            ),
            "reported inflation stayed at or below the matching 100% ceiling": (
                peak_inflation <= MAX_ACCEPTABLE_INFLATION_RATE
            ),
            "player retained seven days of food-and-rent runway": (
                final_player_cash >= ESSENTIAL_DAILY_COST * MIN_PLAYER_RUNWAY_DAYS
            ),
            "kiosk operating gain covered 50% of its advertised minimum profit": (
                # Phase G3: utility fees (~5/day for shop) reduce net profit.
                # Threshold lowered from 75% to 50% to account for utility costs.
                business_operating_gain >= _decimal(blueprint.daily_profit_min) * SIMULATION_DAYS * Decimal("0.50")
            ),
            "kiosk operating gain did not exceed its advertised maximum profit": (
                business_operating_gain <= _decimal(blueprint.daily_profit_max) * SIMULATION_DAYS
            ),
        }
        failed_checks = [name for name, passed in acceptance_checks.items() if not passed]
        assert not failed_checks, f"30-day economy gate failed: {failed_checks}; diagnostics={diagnostics}"
    finally:
        db.close()
