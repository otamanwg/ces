"""
Phase G10 — тести освіти, іспитів, ліцензій, підробного диплома.

Покриває:
- Education: enroll (full_time/part_time limits, duplicate, insufficient funds),
  complete, revoke, list courses, has_completed.
- Exams: take_exam (pass/fail, bribe after 2 fails).
- Licenses: lawyer, police, judge, mayor eligibility.
- Fake diploma: buy, expose, criminal_rep gain.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import Education, EducationExam, Player

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_player(db, city, username="g10player", balance=10000.0) -> Player:
    """Create a player with a custom username/balance (fixture default is 5000.0)."""
    player = Player(
        city_id=city.id,
        username=f"{username}_{__name__}",
        balance=Decimal(str(balance)),
        energy=100,
        mood=80,
        hunger=0,
    )
    db.add(player)
    db.flush()
    return player


# --- Education enrollment ---


class TestEducationEnroll:
    def test_list_courses(self):
        from backend.app.services.education_service import list_courses

        courses = list_courses()
        assert len(courses) == 8
        codes = [c["course"] for c in courses]
        for expected in (
            "economic",
            "legal",
            "police",
            "medical",
            "engineering",
            "journalism",
            "fashion",
            "hospitality",
        ):
            assert expected in codes

    def test_enroll_full_time(self, db, city):
        player = _make_player(db, city, "enroll1", balance=10000.0)
        from backend.app.services.education_service import enroll

        result = enroll(db, player, "economic", "full_time")
        db.flush()
        assert result["success"] is True
        assert player.balance < Decimal("10000.0")  # paid cost

    def test_enroll_part_time(self, db, city):
        player = _make_player(db, city, "enroll2", balance=10000.0)
        from backend.app.services.education_service import enroll

        result = enroll(db, player, "legal", "part_time")
        db.flush()
        assert result["success"] is True

    def test_enroll_one_full_one_part_parallel(self, db, city):
        player = _make_player(db, city, "enroll3", balance=20000.0)
        from backend.app.services.education_service import enroll

        r1 = enroll(db, player, "economic", "full_time")
        r2 = enroll(db, player, "legal", "part_time")
        db.flush()
        assert r1["success"] is True
        assert r2["success"] is True

    def test_cannot_enroll_two_full_time(self, db, city):
        player = _make_player(db, city, "enroll4", balance=30000.0)
        from backend.app.services.education_service import enroll

        enroll(db, player, "economic", "full_time")
        result = enroll(db, player, "legal", "full_time")
        db.flush()
        assert result["success"] is False

    def test_cannot_enroll_two_part_time(self, db, city):
        player = _make_player(db, city, "enroll5", balance=30000.0)
        from backend.app.services.education_service import enroll

        enroll(db, player, "economic", "part_time")
        result = enroll(db, player, "legal", "part_time")
        db.flush()
        assert result["success"] is False

    def test_cannot_enroll_duplicate(self, db, city):
        player = _make_player(db, city, "enroll6", balance=30000.0)
        from backend.app.services.education_service import enroll

        enroll(db, player, "economic", "full_time")
        result = enroll(db, player, "economic", "part_time")
        db.flush()
        assert result["success"] is False

    def test_enroll_insufficient_funds(self, db, city):
        player = _make_player(db, city, "enroll7", balance=100.0)
        from backend.app.services.education_service import enroll

        result = enroll(db, player, "economic", "full_time")
        assert result["success"] is False

    def test_enroll_invalid_course(self, db, city):
        player = _make_player(db, city, "enroll8", balance=10000.0)
        from backend.app.services.education_service import enroll

        result = enroll(db, player, "sports", "full_time")
        assert result["success"] is False


# --- Education completion ---


class TestEducationComplete:
    def test_complete_education(self, db, city):
        player = _make_player(db, city, "comp1", balance=10000.0)
        from backend.app.services.education_service import complete_education, enroll

        enroll_result = enroll(db, player, "economic", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        result = complete_education(db, edu)
        db.flush()
        assert result["success"] is True
        assert edu.status == "completed"
        assert edu.completed_at is not None

    def test_complete_already_completed(self, db, city):
        player = _make_player(db, city, "comp2", balance=10000.0)
        from backend.app.services.education_service import complete_education, enroll

        enroll_result = enroll(db, player, "economic", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        result = complete_education(db, edu)
        assert result["success"] is False

    def test_revoke_education(self, db, city):
        player = _make_player(db, city, "comp3", balance=10000.0)
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            revoke_education,
        )

        enroll_result = enroll(db, player, "legal", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        result = revoke_education(db, edu, "exposed_fake")
        db.flush()
        assert result["success"] is True
        assert edu.status == "revoked"

    def test_has_completed(self, db, city):
        player = _make_player(db, city, "comp4", balance=10000.0)
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            has_completed,
        )

        assert has_completed(db, player, "economic") is False
        enroll_result = enroll(db, player, "economic", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        assert has_completed(db, player, "economic") is True


# --- Exams ---


class TestExams:
    def test_take_exam(self, db, city):
        player = _make_player(db, city, "exam1", balance=10000.0)
        from backend.app.services.education_service import take_exam

        result = take_exam(db, player, "lawyer_license", game_day=1)
        db.flush()
        assert result["success"] is True
        assert "is_passed" in result
        exam = db.query(EducationExam).first()
        assert exam is not None

    def test_bribe_requires_two_fails(self, db, city):
        player = _make_player(db, city, "exam2", balance=10000.0)
        from backend.app.services.education_service import bribe_exam

        # No fails yet
        result = bribe_exam(db, player, "lawyer_license")
        assert result["success"] is False

    def test_bribe_after_fails(self, db, city):
        player = _make_player(db, city, "exam3", balance=10000.0)
        from backend.app.services.education_service import bribe_exam

        # Force 2 fails by inserting failed exams
        for _ in range(2):
            db.add(
                EducationExam(
                    player_id=player.id,
                    exam_type="lawyer_license",
                    is_passed=False,
                )
            )
        db.flush()
        result = bribe_exam(db, player, "lawyer_license")
        db.flush()
        assert result["success"] is True
        assert "is_passed" in result

    def test_bribe_insufficient_funds(self, db, city):
        player = _make_player(db, city, "exam4", balance=10.0)
        from backend.app.services.education_service import bribe_exam

        for _ in range(2):
            db.add(
                EducationExam(
                    player_id=player.id,
                    exam_type="lawyer_license",
                    is_passed=False,
                )
            )
        db.flush()
        result = bribe_exam(db, player, "lawyer_license")
        assert result["success"] is False


# --- Licenses ---


class TestLicenses:
    def test_lawyer_license_requires_education(self, db, city):
        player = _make_player(db, city, "lic1", balance=10000.0)
        from backend.app.services.education_service import issue_lawyer_license

        result = issue_lawyer_license(db, player)
        assert result["success"] is False

    def test_lawyer_license_with_education_and_exam(self, db, city):
        player = _make_player(db, city, "lic2", balance=50000.0)
        from backend.app.models import EducationExam
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            issue_lawyer_license,
        )

        enroll_result = enroll(db, player, "legal", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        # Add a passed exam
        db.add(
            EducationExam(
                player_id=player.id,
                exam_type="lawyer_license",
                is_passed=True,
            )
        )
        db.flush()
        result = issue_lawyer_license(db, player)
        assert result["success"] is True

    def test_police_qualification(self, db, city):
        player = _make_player(db, city, "lic3", balance=50000.0)
        from backend.app.models import EducationExam
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            issue_police_qualification,
        )

        enroll_result = enroll(db, player, "police", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        db.add(
            EducationExam(
                player_id=player.id,
                exam_type="police_qualification",
                is_passed=True,
            )
        )
        db.flush()
        result = issue_police_qualification(db, player)
        assert result["success"] is True

    def test_judge_qualification(self, db, city):
        player = _make_player(db, city, "lic4", balance=50000.0)
        from backend.app.models import EducationExam
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            issue_judge_qualification,
        )

        enroll_result = enroll(db, player, "legal", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == enroll_result["education_id"]).first()
        complete_education(db, edu)
        db.add(
            EducationExam(
                player_id=player.id,
                exam_type="judge_qualification",
                is_passed=True,
            )
        )
        db.flush()
        result = issue_judge_qualification(db, player)
        assert result["success"] is True

    def test_mayor_eligibility_not_eligible(self, db, city):
        player = _make_player(db, city, "lic5", balance=50000.0)
        from backend.app.services.education_service import check_mayor_eligibility

        result = check_mayor_eligibility(db, player)
        assert result["eligible"] is False

    def test_mayor_eligibility_with_education_and_practice(self, db, city):
        player = _make_player(db, city, "lic6", balance=100000.0)
        from backend.app.services.education_service import (
            check_mayor_eligibility,
            complete_education,
            enroll,
        )

        # Complete economic + legal
        for course in ("economic", "legal"):
            r = enroll(db, player, course, "full_time")
            db.flush()
            edu = db.query(Education).filter(Education.id == r["education_id"]).first()
            complete_education(db, edu)
        # Set practice
        player.successful_deals = 100
        db.flush()
        result = check_mayor_eligibility(db, player)
        assert result["eligible"] is True


# --- Fake diploma ---


class TestFakeDiploma:
    def test_buy_fake_diploma(self, db, city):
        player = _make_player(db, city, "fake1", balance=10000.0)
        from backend.app.services.education_service import (
            buy_fake_diploma,
            has_completed,
        )

        result = buy_fake_diploma(db, player, "economic")
        db.flush()
        assert result["success"] is True
        assert player.criminal_rep > 0
        assert has_completed(db, player, "economic") is True
        edu = db.query(Education).filter(Education.player_id == player.id).first()
        assert edu.is_fake is True

    def test_buy_fake_diploma_insufficient_funds(self, db, city):
        player = _make_player(db, city, "fake2", balance=100.0)
        from backend.app.services.education_service import buy_fake_diploma

        result = buy_fake_diploma(db, player, "economic")
        assert result["success"] is False

    def test_buy_fake_diploma_duplicate(self, db, city):
        player = _make_player(db, city, "fake3", balance=20000.0)
        from backend.app.services.education_service import buy_fake_diploma

        buy_fake_diploma(db, player, "economic")
        db.flush()
        result = buy_fake_diploma(db, player, "economic")
        assert result["success"] is False

    def test_expose_fake_diploma(self, db, city):
        player = _make_player(db, city, "fake4", balance=10000.0)
        from backend.app.services.education_service import (
            buy_fake_diploma,
            expose_fake_diploma,
        )

        buy_fake_diploma(db, player, "legal")
        db.flush()
        edu = db.query(Education).filter(Education.player_id == player.id).first()
        result = expose_fake_diploma(db, edu)
        assert result["success"] is True
        # Per gameplay model: exposure does NOT block diploma
        assert edu.status == "completed"

    def test_expose_real_diploma_fails(self, db, city):
        player = _make_player(db, city, "fake5", balance=10000.0)
        from backend.app.services.education_service import (
            complete_education,
            enroll,
            expose_fake_diploma,
        )

        r = enroll(db, player, "economic", "full_time")
        db.flush()
        edu = db.query(Education).filter(Education.id == r["education_id"]).first()
        complete_education(db, edu)
        result = expose_fake_diploma(db, edu)
        assert result["success"] is False
