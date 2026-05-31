import os
from decimal import Decimal

import pytest

from backend.app.models import City, Hostel, Job, Player
from backend.app.seed import seed_initial_data
from backend.app.services.player_progress import build_goal_effects
from backend.tests.db import make_test_session


TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _next_action(effects: list[dict]) -> dict | None:
    return next((effect for effect in effects if effect["key"] == "next_action"), None)


def test_next_action_suggests_apply_without_job():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-no-job",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Влаштуйтесь на роботу"
    finally:
        db.close()


def test_next_action_suggests_sleep_when_tired():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-tired",
            balance=Decimal("500.00"),
            energy=20,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Спати (оренда + відновлення)"
        assert "30" in (hint.get("delta") or "")
    finally:
        db.close()


def test_next_action_suggests_work_when_ready():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-work",
            balance=Decimal("50.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Відпрацюйте зміну"
        assert hint["delta"] == job.title
    finally:
        db.close()


def test_next_action_suggests_exam_when_affordable():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-exam",
            balance=Decimal("150.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Складіть іспит у коледж"
    finally:
        db.close()


def test_next_action_suggests_college_job_after_diploma():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-college",
            balance=Decimal("200.00"),
            energy=100,
            mood=100,
            education_level="College",
        )
        db.add(player)
        db.flush()

        hs_job = db.query(Job).filter(Job.min_education == "High School").first()
        hs_job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Влаштуйтесь на кращу посаду"
        assert "Диспетчер" in (hint.get("delta") or "")
    finally:
        db.close()
