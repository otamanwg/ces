import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, City, Hostel, Job, Player, TransactionModelLog
from backend.app.seed import seed_initial_data
from backend.app.services.economy import game_day_tick, process_rent_payment, process_shift_work


TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def make_session():
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.execute(text("GRANT ALL ON SCHEMA public TO city"))
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_seed_creates_core_city_data():
    db = make_session()
    try:
        seed_initial_data(db)

        assert db.query(City).count() == 1
        assert db.query(Job).count() == 3
        assert db.query(Hostel).count() == 5
    finally:
        db.close()


def test_work_and_sleep_loop_updates_player_and_logs_transactions():
    db = make_session()
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
        assert work_result["player"]["balance"] > 500

        sleep_result = process_rent_payment(db, str(player.id))
        assert sleep_result["success"] is True
        assert sleep_result["player"]["energy"] == 100
        assert db.query(TransactionModelLog).count() == 2
    finally:
        db.close()


def test_game_day_tick_keeps_30_day_balance_stable():
    db = make_session()
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

        db.refresh(player)
        db.refresh(city)

        assert player.balance == starting_player_balance - Decimal("450.00")
        assert player.energy == 0
        assert player.mood >= 10
        assert city.inflation_rate >= 0
        assert Decimal(str(last_result["stats"]["active_money_after"])) <= starting_active_money
        assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "daily_rent").count() == 30
    finally:
        db.close()
