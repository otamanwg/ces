import os
from decimal import Decimal

import pytest

from backend.app.models import Business, BusinessBlueprint, City, CityDistrict, Hostel, Job, LandParcel, Player, SportsClub, TransactionModelLog
from backend.app.schemas.service_results import (
    BusinessDividendServiceResult,
    BusinessPurchaseServiceResult,
    DayTickServiceResult,
    ExamSubmissionServiceResult,
    MealPurchaseServiceResult,
    SportsContractServiceResult,
    SportsLeagueMatchServiceResult,
    RentPaymentServiceResult,
    SportsTrainServiceResult,
    WorkShiftServiceResult,
)
from backend.app.seed import seed_initial_data
from backend.app.services.business_market import (
    get_buyable_businesses,
    process_business_dividend_collection,
    process_business_purchase,
)
from backend.app.services.economy import game_day_tick, process_rent_payment, process_shift_work
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.needs import process_meal_purchase
from backend.app.services.sports import sign_athlete_contract, simulate_league_matches, train_at_gym
from backend.tests.db import make_test_session


TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def test_seed_creates_core_city_data():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        assert db.query(City).count() == 1
        assert db.query(BusinessBlueprint).count() == 7
        assert db.query(CityDistrict).count() == 6
        assert db.query(LandParcel).count() == 6
        assert db.query(Job).count() == 3
        assert db.query(Hostel).count() == 5
        assert len(get_buyable_businesses(db)) == 1
        districts = db.query(CityDistrict).order_by(CityDistrict.display_order).all()
        assert [district.code for district in districts] == [
            "bus_station",
            "commercial_core",
            "highrise_residential",
            "industrial_edge",
            "suburb_private_sector",
            "outer_land",
        ]
        assert all(0 <= district.medical_coverage <= 100 for district in districts)
        assert districts[-1].land_available_hectares == Decimal("250.00")
        parcels = db.query(LandParcel).order_by(LandParcel.current_price).all()
        assert parcels[0].code == "bus_station_kiosk_lot"
        assert parcels[0].current_price == Decimal("200.00")
        assert all(parcel.status == "city_owned" for parcel in parcels)
    finally:
        db.close()


def test_seed_backfills_districts_for_existing_city():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        city = City(name="Existing Dev City")
        db.add(city)
        db.commit()

        seed_initial_data(db)

        assert db.query(City).count() == 1
        assert db.query(BusinessBlueprint).count() == 7
        assert db.query(CityDistrict).count() == 6
        seed_initial_data(db)
        assert db.query(BusinessBlueprint).count() == 7
        assert db.query(CityDistrict).count() == 6
        assert db.query(LandParcel).count() == 6

        missing = db.query(CityDistrict).filter(CityDistrict.code == "outer_land").one()
        db.delete(missing)
        db.commit()
        assert db.query(CityDistrict).count() == 5
        assert db.query(LandParcel).count() == 5

        seed_initial_data(db)
        assert db.query(CityDistrict).count() == 6
        assert db.query(LandParcel).count() == 6

        missing_parcel = db.query(LandParcel).filter(LandParcel.code == "outer_expansion_lot").one()
        db.delete(missing_parcel)
        db.commit()
        assert db.query(LandParcel).count() == 5

        seed_initial_data(db)
        assert db.query(LandParcel).count() == 6
    finally:
        db.close()


def test_work_and_sleep_loop_updates_player_and_logs_transactions():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="test-player",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id

        job = db.query(Job).filter(Job.min_education == "High School").order_by(Job.salary_per_hour).first()
        job.filled_by_player_id = player.id
        db.commit()
        starting_treasury = Decimal(str(city.treasury_balance))

        work_result = process_shift_work(db, str(player.id))
        assert work_result["success"] is True
        WorkShiftServiceResult.model_validate(work_result)
        assert work_result["player"]["energy"] == 70
        assert work_result["player"]["hunger"] == 20
        assert work_result["player"]["balance"] > 500
        db.refresh(city)
        assert Decimal(str(city.treasury_balance)) == starting_treasury - Decimal("180.00")

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        RentPaymentServiceResult.model_validate(sleep_result)
        assert sleep_result["player"]["energy"] == 100
        assert sleep_result["player"]["hunger"] == 30
        db.refresh(city)
        assert Decimal(str(city.treasury_balance)) == starting_treasury - Decimal("165.00")
        assert db.query(TransactionModelLog).count() == 2

        salary_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "salary").one()
        assert salary_log.sender_id == city.id
        assert salary_log.sender_type == "treasury"
        assert salary_log.receiver_id == player.id
        assert salary_log.receiver_type == "player"
        assert salary_log.amount == Decimal("180.00")
        assert salary_log.tax_deducted == Decimal("20.00")

        rent_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "rent").one()
        assert rent_log.sender_id == player.id
        assert rent_log.sender_type == "player"
        assert rent_log.receiver_id == city.id
        assert rent_log.receiver_type == "treasury"
        assert rent_log.amount == Decimal("15.00")
    finally:
        db.close()


def test_meal_purchase_reduces_hunger_charges_player_and_logs_food():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hungry-player",
            balance=Decimal("100.00"),
            energy=100,
            mood=80,
            hunger=80,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        starting_treasury = Decimal(str(city.treasury_balance))
        meal_result = process_meal_purchase(db, str(player.id))

        assert meal_result["success"] is True
        MealPurchaseServiceResult.model_validate(meal_result)
        db.refresh(player)
        db.refresh(city)
        assert Decimal(str(player.balance)) == Decimal("75.00")
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("25.00")
        assert player.hunger == 45
        assert player.mood == 85

        food_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "food").one()
        assert food_log.sender_id == player.id
        assert food_log.sender_type == "player"
        assert food_log.receiver_id == city.id
        assert food_log.receiver_type == "treasury"
        assert food_log.amount == Decimal("25.00")
    finally:
        db.close()


def test_private_business_shift_pays_worker_from_business_cash_and_taxes_city():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        owner = Player(
            city_id=city.id,
            username="private-owner",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        worker = Player(
            city_id=city.id,
            username="private-worker",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add_all([owner, worker])
        db.flush()

        business = db.query(Business).filter(Business.type == "shop").one()
        business.owner_player_id = owner.id
        business.cash_balance = Decimal("1000.00")
        job = Job(
            business_id=business.id,
            title="Бариста",
            salary_per_hour=Decimal("10.00"),
            min_education="High School",
            energy_cost_per_shift=20,
            filled_by_player_id=worker.id,
        )
        db.add(job)
        db.commit()

        starting_treasury = Decimal(str(city.treasury_balance))
        result = process_shift_work(db, str(worker.id))

        assert result["success"] is True
        WorkShiftServiceResult.model_validate(result)
        db.refresh(worker)
        db.refresh(business)
        db.refresh(city)
        assert Decimal(str(worker.balance)) == Decimal("172.00")
        assert Decimal(str(business.cash_balance)) == Decimal("920.00")
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("8.00")

        salary_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "salary").one()
        assert salary_log.sender_id == business.id
        assert salary_log.sender_type == "business"
        assert salary_log.receiver_id == worker.id
        assert salary_log.receiver_type == "player"
        assert salary_log.amount == Decimal("72.00")
        assert salary_log.tax_deducted == Decimal("8.00")
    finally:
        db.close()


def test_business_purchase_transfers_money_to_treasury_and_assigns_owner():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        business = db.query(Business).filter(Business.type == "shop").one()
        player = Player(
            city_id=city.id,
            username="business-buyer",
            balance=Decimal("1500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        starting_treasury = Decimal(str(city.treasury_balance))
        result = process_business_purchase(db, str(player.id), str(business.id))

        assert result["success"] is True
        BusinessPurchaseServiceResult.model_validate(result)
        db.refresh(player)
        db.refresh(city)
        db.refresh(business)
        assert business.owner_player_id == player.id
        assert Decimal(str(player.balance)) == Decimal("300.00")
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("1200.00")

        purchase_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "business_purchase").one()
        assert purchase_log.sender_id == player.id
        assert purchase_log.sender_type == "player"
        assert purchase_log.receiver_id == city.id
        assert purchase_log.receiver_type == "treasury"
        assert purchase_log.amount == Decimal("1200.00")
    finally:
        db.close()


def test_business_dividend_moves_cash_from_owned_business_to_player():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        business = db.query(Business).filter(Business.type == "shop").one()
        player = Player(
            city_id=city.id,
            username="dividend-owner",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()
        business.owner_player_id = player.id
        db.commit()

        result = process_business_dividend_collection(db, str(player.id), str(business.id))

        assert result["success"] is True
        BusinessDividendServiceResult.model_validate(result)
        db.refresh(player)
        db.refresh(business)
        assert Decimal(str(player.balance)) == Decimal("200.00")
        assert Decimal(str(business.cash_balance)) == Decimal("900.00")

        dividend_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "business_dividend").one()
        assert dividend_log.sender_id == business.id
        assert dividend_log.sender_type == "business"
        assert dividend_log.receiver_id == player.id
        assert dividend_log.receiver_type == "player"
        assert dividend_log.amount == Decimal("100.00")
    finally:
        db.close()


def test_gym_training_charges_player_treasury_and_logs_fee():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        club = db.query(SportsClub).first()
        player = Player(
            city_id=city.id,
            username="gym-player",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        contract_result = sign_athlete_contract(db, str(player.id), str(club.id), 120.0)
        assert contract_result["success"] is True
        SportsContractServiceResult.model_validate(contract_result)
        starting_treasury = Decimal(str(city.treasury_balance))

        result = train_at_gym(db, str(player.id), "strength")

        assert result["success"] is True
        SportsTrainServiceResult.model_validate(result)
        db.refresh(player)
        db.refresh(city)
        assert Decimal(str(player.balance)) == Decimal("60.00")
        assert player.energy == 60
        assert result["stats"]["strength"] >= 12
        assert result["stats"]["strength"] <= 15
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("40.00")

        gym_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "gym_training").one()
        assert gym_log.sender_id == player.id
        assert gym_log.sender_type == "player"
        assert gym_log.receiver_id == city.id
        assert gym_log.receiver_type == "treasury"
        assert gym_log.amount == Decimal("40.00")
    finally:
        db.close()


def test_sports_matches_create_ticket_revenue_and_pay_winning_athlete(monkeypatch):
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        club = db.query(SportsClub).first()
        player = Player(
            city_id=city.id,
            username="match-athlete",
            balance=Decimal("50.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        contract_result = sign_athlete_contract(db, str(player.id), str(club.id), 120.0)
        assert contract_result["success"] is True
        SportsContractServiceResult.model_validate(contract_result)
        starting_club_cash = Decimal(str(club.cash_balance))

        monkeypatch.setattr("backend.app.services.sports.random.randint", lambda _start, _end: 1)
        results = simulate_league_matches(db, str(city.id))

        assert len(results) == 3
        for result in results:
            SportsLeagueMatchServiceResult.model_validate(result)
        db.refresh(player)
        db.refresh(club)
        assert Decimal(str(player.balance)) == Decimal("290.00")
        assert Decimal(str(club.cash_balance)) > starting_club_cash

        ticket_logs = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "ticket_revenue").all()
        assert len(ticket_logs) == 3
        assert all(log.receiver_type == "business" for log in ticket_logs)

        salary_logs = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "athlete_match_salary").all()
        assert len(salary_logs) == 2
        assert all(log.sender_id == club.id for log in salary_logs)
        assert all(log.receiver_id == player.id for log in salary_logs)
        assert sum(Decimal(str(log.amount)) for log in salary_logs) == Decimal("240.00")
    finally:
        db.close()


def test_game_day_tick_applies_decay_without_rent():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="balance-test-player",
            balance=Decimal("1000.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id
        db.commit()

        starting_player_balance = Decimal(str(player.balance))
        starting_active_money = Decimal(str(player.balance))

        last_result = None
        for _ in range(30):
            last_result = game_day_tick(db, str(city.id))
            assert last_result["success"] is True
            DayTickServiceResult.model_validate(last_result)
            assert last_result["stats"]["rent_collected"] == 0.0
            assert "hungry_players" in last_result["stats"]

        db.refresh(player)
        db.refresh(city)

        assert player.balance == starting_player_balance
        assert player.energy == 0
        assert player.mood >= 10
        assert city.inflation_rate >= 0
        assert Decimal(str(last_result["stats"]["active_money_after"])) == starting_active_money
        assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "daily_rent").count() == 0
    finally:
        db.close()


def test_sleep_then_tick_does_not_double_charge_rent():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="no-double-rent-player",
            balance=Decimal("500.00"),
            energy=70,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id
        db.commit()

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        RentPaymentServiceResult.model_validate(sleep_result)

        db.refresh(player)
        balance_after_sleep = Decimal(str(player.balance))
        rent_logs = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "rent").count()
        assert rent_logs == 1

        tick_result = game_day_tick(db, str(city.id))
        assert tick_result["success"] is True
        DayTickServiceResult.model_validate(tick_result)
        assert tick_result["stats"]["rent_collected"] == 0.0

        db.refresh(player)
        assert player.balance == balance_after_sleep
        assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "rent").count() == 1
        assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "daily_rent").count() == 0
    finally:
        db.close()


def test_exam_payment_updates_treasury_and_logs_fee():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="exam-ledger-player",
            balance=Decimal("700.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        exam = load_manager_exam()
        answers = {str(q["id"]): q["correct_option_index"] for q in exam["questions"]}
        exam_cost = Decimal(str(exam["cost_to_take"]))
        starting_player_balance = Decimal(str(player.balance))
        starting_treasury = Decimal(str(city.treasury_balance))

        result = process_exam_submission(db, str(player.id), answers)
        assert result["success"] is True
        assert result["passed"] is True

        db.refresh(player)
        db.refresh(city)
        assert Decimal(str(player.balance)) == starting_player_balance - exam_cost
        assert Decimal(str(city.treasury_balance)) == starting_treasury + exam_cost

        exam_fee = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "exam_fee").one()
        assert exam_fee.sender_id == player.id
        assert exam_fee.sender_type == "player"
        assert exam_fee.receiver_id == city.id
        assert exam_fee.receiver_type == "treasury"
        assert exam_fee.amount == exam_cost
        assert exam_fee.tax_deducted == Decimal("0.00")
    finally:
        db.close()


def test_starter_balance_reaches_college_after_one_work_sleep_cycle():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="starter-balance-loop",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id
        job = db.query(Job).filter(Job.min_education == "High School").order_by(Job.salary_per_hour).first()
        job.filled_by_player_id = player.id
        db.commit()

        exam = load_manager_exam()
        answers = {str(q["id"]): q["correct_option_index"] for q in exam["questions"]}
        exam_cost = Decimal(str(exam["cost_to_take"]))
        assert Decimal(str(player.balance)) < exam_cost

        work_result = process_shift_work(db, str(player.id))
        assert work_result["success"] is True
        WorkShiftServiceResult.model_validate(work_result)
        db.refresh(player)
        assert Decimal(str(player.balance)) == Decimal("680.00")
        assert player.energy == 70

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        RentPaymentServiceResult.model_validate(sleep_result)
        db.refresh(player)
        assert Decimal(str(player.balance)) == Decimal("665.00")
        assert player.energy == 100
        assert Decimal(str(player.balance)) >= exam_cost

        exam_result = process_exam_submission(db, str(player.id), answers)
        assert exam_result["success"] is True
        ExamSubmissionServiceResult.model_validate(exam_result)
        assert exam_result["passed"] is True
        db.refresh(player)
        assert player.education_level == "College"
        assert Decimal(str(player.balance)) == Decimal("15.00")

        purposes = [row.purpose for row in db.query(TransactionModelLog).order_by(TransactionModelLog.timestamp).all()]
        assert purposes == ["salary", "rent", "exam_fee"]
    finally:
        db.close()
