import os
from decimal import Decimal

import pytest

from backend.app.models import Business, City, Hostel, Job, Player, SportsClub
from backend.app.schemas.mvp import PlayerSnapshotData
from backend.app.seed import seed_initial_data
from backend.app.services.economy import process_rent_payment, process_shift_work
from backend.app.services.education import load_manager_exam, process_exam_submission
from backend.app.services.player_profile import build_player_snapshot
from backend.app.services.player_progress import build_goal_effects
from backend.app.services.sports import GYM_COST, GYM_ENERGY_COST, sign_athlete_contract
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
            balance=Decimal("700.00"),
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


def test_player_snapshot_actions_follow_current_state():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="snapshot-actions",
            balance=Decimal("50.00"),
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

        snapshot = build_player_snapshot(db, player)
        assert snapshot["actions"] == {
            "can_apply_job": True,
            "can_work": True,
            "can_sleep": True,
            "can_eat": False,
            "can_buy_business": False,
            "can_collect_dividend": False,
            "can_join_sports": True,
            "can_train_sports": False,
            "can_take_exam": False,
        }

        player.energy = 10
        player.balance = Decimal("1500.00")
        player.hunger = 40
        db.commit()

        snapshot = build_player_snapshot(db, player)
        assert snapshot["actions"]["can_work"] is False
        assert snapshot["actions"]["can_sleep"] is True
        assert snapshot["actions"]["can_eat"] is True
        assert snapshot["actions"]["can_buy_business"] is True
        assert snapshot["actions"]["can_collect_dividend"] is False
        assert snapshot["actions"]["can_join_sports"] is True
        assert snapshot["actions"]["can_train_sports"] is False
        assert snapshot["actions"]["can_take_exam"] is True
    finally:
        db.close()


def test_player_snapshot_matches_contract_with_business_and_sports_data():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="snapshot-contract",
            balance=Decimal("1500.00"),
            energy=100,
            mood=100,
            hunger=20,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id
        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        business = db.query(Business).filter(Business.type == "shop").one()
        business.owner_player_id = player.id
        club = db.query(SportsClub).first()
        db.commit()

        assert sign_athlete_contract(db, str(player.id), str(club.id), 120.0)["success"] is True
        db.refresh(player)

        snapshot = build_player_snapshot(db, player)
        validated = PlayerSnapshotData.model_validate(snapshot)

        assert validated.id == str(player.id)
        assert validated.username == "snapshot-contract"
        assert validated.job_id == str(job.id)
        assert validated.hostel == f"Кімната №{room.room_number} (Хостел)"
        assert validated.owned_businesses[0].id == str(business.id)
        assert validated.owned_businesses[0].name == business.name
        assert validated.sports_contract is not None
        assert validated.sports_contract.club == club.name
        assert validated.sports_contract.salary_per_match == 120.0
        assert validated.actions.can_collect_dividend is True
        assert validated.actions.can_join_sports is False
        assert validated.actions.can_train_sports is True
        assert _next_action(snapshot["goal_effects"]) is not None
    finally:
        db.close()


def test_next_action_suggests_food_when_hunger_is_high():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-hungry",
            balance=Decimal("500.00"),
            energy=100,
            mood=70,
            hunger=75,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        job = db.query(Job).filter(Job.min_education == "High School").first()
        job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Поїжте"
        assert "75/100" in (hint.get("delta") or "")
    finally:
        db.close()


def test_next_action_guides_complete_starter_loop():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="guided-starter-loop",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()

        room = db.query(Hostel).first()
        room.tenant_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Влаштуйтесь на роботу"

        job = db.query(Job).filter(Job.min_education == "High School").order_by(Job.salary_per_hour).first()
        job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Відпрацюйте зміну"
        assert hint["delta"] == job.title

        assert process_shift_work(db, str(player.id))["success"] is True
        db.refresh(player)
        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Складіть іспит у коледж"

        player.energy = 20
        db.commit()
        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Спати (оренда + відновлення)"

        assert process_rent_payment(db, str(player.id))["success"] is True
        db.refresh(player)
        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Складіть іспит у коледж"

        exam = load_manager_exam()
        answers = {str(q["id"]): q["correct_option_index"] for q in exam["questions"]}
        assert process_exam_submission(db, str(player.id), answers)["success"] is True
        db.refresh(player)
        hint = _next_action(build_goal_effects(db, player))
        assert hint["value"] == "Влаштуйтесь на кращу посаду"
        assert "Диспетчер" in (hint.get("delta") or "")
    finally:
        db.close()


def test_next_action_suggests_business_after_core_loop_when_affordable():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-business",
            balance=Decimal("1500.00"),
            energy=100,
            mood=100,
            education_level="College",
        )
        db.add(player)
        db.flush()

        college_job = db.query(Job).filter(Job.min_education == "College").first()
        college_job.filled_by_player_id = player.id
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Купіть перший бізнес"
        assert "1200" in (hint.get("delta") or "")
    finally:
        db.close()


def test_next_action_suggests_dividend_for_owned_business():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-dividend",
            balance=Decimal("200.00"),
            energy=100,
            mood=100,
            education_level="College",
        )
        db.add(player)
        db.flush()

        college_job = db.query(Job).filter(Job.min_education == "College").first()
        college_job.filled_by_player_id = player.id
        business = db.query(Business).filter(Business.type == "shop").one()
        business.owner_player_id = player.id
        business.cash_balance = Decimal("300.00")
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Зберіть дивіденд"
        assert hint["delta"] == business.name
    finally:
        db.close()


def test_next_action_suggests_sports_then_training_after_core_loop():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)
        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="hint-sports",
            balance=Decimal("200.00"),
            energy=100,
            mood=100,
            education_level="College",
        )
        db.add(player)
        db.flush()

        college_job = db.query(Job).filter(Job.min_education == "College").first()
        college_job.filled_by_player_id = player.id
        club = db.query(SportsClub).first()
        db.commit()

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Підпишіть спортивний контракт"

        assert sign_athlete_contract(db, str(player.id), str(club.id), 120.0)["success"] is True
        player.balance = GYM_COST
        player.energy = GYM_ENERGY_COST
        db.commit()
        db.refresh(player)

        hint = _next_action(build_goal_effects(db, player))
        assert hint is not None
        assert hint["value"] == "Потренуйтесь у спортзалі"
        assert "40" in (hint.get("delta") or "")
    finally:
        db.close()
