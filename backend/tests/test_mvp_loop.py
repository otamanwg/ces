import os
from decimal import Decimal

import pytest

from backend.app.models import City, Hostel, Job, Player, TransactionModelLog
from backend.app.seed import seed_initial_data
from backend.app.services.economy import game_day_tick, process_rent_payment, process_shift_work
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.needs import process_meal_purchase
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
        assert db.query(Job).count() == 3
        assert db.query(Hostel).count() == 5
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

        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        db.commit()

        work_result = process_shift_work(db, str(player.id))
        assert work_result["success"] is True
        assert work_result["player"]["energy"] == 70
        assert work_result["player"]["hunger"] == 20
        assert work_result["player"]["balance"] > 500

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        assert sleep_result["player"]["energy"] == 100
        assert sleep_result["player"]["hunger"] == 30
        assert db.query(TransactionModelLog).count() == 2
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
            assert last_result["stats"]["rent_collected"] == 0.0

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

        db.refresh(player)
        balance_after_sleep = Decimal(str(player.balance))
        rent_logs = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "rent").count()
        assert rent_logs == 1

        tick_result = game_day_tick(db, str(city.id))
        assert tick_result["success"] is True
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
        db.refresh(player)
        assert Decimal(str(player.balance)) == Decimal("680.00")
        assert player.energy == 70

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        db.refresh(player)
        assert Decimal(str(player.balance)) == Decimal("665.00")
        assert player.energy == 100
        assert Decimal(str(player.balance)) >= exam_cost

        exam_result = process_exam_submission(db, str(player.id), answers)
        assert exam_result["success"] is True
        assert exam_result["passed"] is True
        db.refresh(player)
        assert player.education_level == "College"
        assert Decimal(str(player.balance)) == Decimal("15.00")

        purposes = [row.purpose for row in db.query(TransactionModelLog).order_by(TransactionModelLog.timestamp).all()]
        assert purposes == ["salary", "rent", "exam_fee"]
    finally:
        db.close()
