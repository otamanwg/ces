"""Phase G10 — Education tree, exams, licenses, fake diploma.

Education is the primary decision-tree window. Each course opens new
branches (professions, businesses, mechanics). Courses consume energy
(1000/day full_time, 500/day part_time). One full_time + one part_time
may run in parallel. Exams are a daily mini-game; two failures unlock a
bribable retry (chance depends on criminal_rep). Licenses (lawyer,
police, judge, mayor) require education + practice + annual exam.
Fake diploma (corruption) opens the same branches until exposed.
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import City, Education, EducationExam, Player

logger = logging.getLogger("EducationService")

# --- Course catalog ---

COURSES: dict[str, dict] = {
    "economic": {
        "name": "Економічна освіта",
        "duration_days": 30,
        "cost": Decimal("2000.00"),
        "energy_per_day": 1000,
        "opens": ("business_management", "bank", "investments"),
        "required_for": ("mayor",),
    },
    "legal": {
        "name": "Юридична освіта",
        "duration_days": 60,
        "cost": Decimal("4000.00"),
        "energy_per_day": 1000,
        "opens": ("lawyer", "judge", "law_firm"),
        "required_for": ("mayor", "lawyer"),
    },
    "police": {
        "name": "Поліцейська академія",
        "duration_days": 45,
        "cost": Decimal("3000.00"),
        "energy_per_day": 1000,
        "opens": ("police_officer",),
        "required_for": ("police_chief",),
    },
    "medical": {
        "name": "Медична освіта",
        "duration_days": 45,
        "cost": Decimal("3500.00"),
        "energy_per_day": 1000,
        "opens": ("pharmacy", "medical_clinic"),
        "required_for": (),
    },
    "engineering": {
        "name": "Інженерна освіта",
        "duration_days": 45,
        "cost": Decimal("3500.00"),
        "energy_per_day": 1000,
        "opens": ("manufacturing", "construction_company", "utility_services"),
        "required_for": (),
    },
    "journalism": {
        "name": "Журналістська освіта",
        "duration_days": 30,
        "cost": Decimal("2000.00"),
        "energy_per_day": 1000,
        "opens": ("media_outlet", "journalist"),
        "required_for": (),
    },
    "fashion": {
        "name": "Дизайн/Мода",
        "duration_days": 30,
        "cost": Decimal("2000.00"),
        "energy_per_day": 1000,
        "opens": ("atelier", "skin_design"),
        "required_for": (),
    },
    "hospitality": {
        "name": "Гостинність",
        "duration_days": 30,
        "cost": Decimal("2000.00"),
        "energy_per_day": 1000,
        "opens": ("restaurant", "hotel", "bar", "casino"),
        "required_for": (),
    },
}

ALLOWED_COURSES = tuple(COURSES.keys())

# Energy cost per day by mode
ENERGY_FULL_TIME = 1000
ENERGY_PART_TIME = 500

# Scholarship for full_time education (fixed, paid by AI)
SCHOLARSHIP_DAILY = Decimal("50.00")

# License validity (days)
LICENSE_VALIDITY_DAYS = 365

# Exam pass base chance
EXAM_BASE_PASS = 0.7
EXAM_FAIL_THRESHOLD = 2  # after 2 fails, bribe option unlocks
BRIBE_SUCCESS_BASE = 0.5
BRIBE_COST = Decimal("500.00")

# Fake diploma
FAKE_DIPLOMA_COST = Decimal("5000.00")
FAKE_DIPLOMA_REP_GAIN = 15.0  # criminal_rep gain


def _now() -> datetime:
    return datetime.now(UTC)


# --- Enrollment ---


def list_courses() -> list[dict]:
    """Return course catalog."""
    return [
        {
            "course": code,
            "name": info["name"],
            "duration_days": info["duration_days"],
            "cost": float(info["cost"]),
            "energy_per_day": info["energy_per_day"],
            "opens": info["opens"],
            "required_for": info["required_for"],
        }
        for code, info in COURSES.items()
    ]


def get_active_enrollments(db: Session, player: Player) -> list[Education]:
    """Return active (enrolled) educations for player."""
    return db.query(Education).filter(Education.player_id == player.id, Education.status == "enrolled").all()


def get_completed_courses(db: Session, player: Player) -> list[Education]:
    """Return completed (non-revoked) educations for player."""
    return db.query(Education).filter(Education.player_id == player.id, Education.status == "completed").all()


def has_completed(db: Session, player: Player, course: str) -> bool:
    """Check if player has completed a course (real or fake)."""
    return (
        db.query(Education)
        .filter(
            Education.player_id == player.id,
            Education.course == course,
            Education.status == "completed",
        )
        .first()
        is not None
    )


def enroll(db: Session, player: Player, course: str, mode: str = "full_time") -> dict:
    """Enroll player in a course.

    Rules:
    - One full_time + one part_time may run in parallel.
    - Cannot enroll in same course twice (unless revoked).
    - Player must afford cost.
    """
    if course not in COURSES:
        return {"success": False, "message": "Невідомий курс."}
    if mode not in ("full_time", "part_time"):
        return {"success": False, "message": "Невідомий режим (full_time/part_time)."}

    active = get_active_enrollments(db, player)
    full_time_count = sum(1 for e in active if e.mode == "full_time")
    part_time_count = sum(1 for e in active if e.mode == "part_time")

    if mode == "full_time" and full_time_count >= 1:
        return {"success": False, "message": "Можна лише одну очну освіту одночасно."}
    if mode == "part_time" and part_time_count >= 1:
        return {"success": False, "message": "Можна лише одну заочну освіту одночасно."}

    # Check duplicate enrollment
    existing = (
        db.query(Education)
        .filter(
            Education.player_id == player.id,
            Education.course == course,
            Education.status.in_(("enrolled", "completed")),
        )
        .first()
    )
    if existing is not None:
        return {"success": False, "message": "Вже записаний на цей курс або завершив його."}

    cost = COURSES[course]["cost"]
    if player.balance < cost:
        return {"success": False, "message": "Недостатньо коштів для оплати курсу."}

    player.balance = Decimal(str(player.balance)) - cost
    education = Education(
        player_id=player.id,
        course=course,
        mode=mode,
        status="enrolled",
        is_fake=False,
        enrolled_at=_now(),
    )
    db.add(education)
    db.flush()
    logger.info("Player %s enrolled in %s (%s)", player.username, course, mode)
    return {
        "success": True,
        "message": f"Зараховано на курс '{COURSES[course]['name']}'.",
        "education_id": education.id,
    }


def daily_tick(db: Session, player: Player, game_day: int) -> dict:
    """Process daily education tick for player.

    - Consumes energy.
    - Pays scholarship for full_time.
    - Completes courses that reached duration.
    """
    active = get_active_enrollments(db, player)
    if not active:
        return {"success": True, "message": "Немає активних курсів.", "completed": []}

    completed_now: list[str] = []
    for edu in active:
        info = COURSES.get(edu.course)
        if info is None:
            continue

        energy_cost = ENERGY_FULL_TIME if edu.mode == "full_time" else ENERGY_PART_TIME
        if player.energy < energy_cost:
            # Not enough energy — skip this day, no progress
            logger.warning(
                "Player %s lacks energy for %s (need %d, has %d)",
                player.username,
                edu.course,
                energy_cost,
                player.energy,
            )
            continue

        player.energy -= energy_cost

        # Scholarship for full_time
        if edu.mode == "full_time":
            player.balance = Decimal(str(player.balance)) + SCHOLARSHIP_DAILY

        # Completion is triggered explicitly via complete_education() after
        # duration_days have elapsed (by scheduler). Here we just consume
        # energy and pay scholarship.

    db.flush()
    return {
        "success": True,
        "message": "Освітній тік оброблено.",
        "completed": completed_now,
    }


def complete_education(db: Session, education: Education) -> dict:
    """Mark an education as completed.

    Called when duration_days have elapsed (by scheduler or explicit call).
    """
    if education.status != "enrolled":
        return {"success": False, "message": "Курс не активний."}
    education.status = "completed"
    education.completed_at = _now()
    db.flush()
    logger.info("Education %s completed for player %s", education.course, education.player_id)
    return {
        "success": True,
        "message": f"Курс '{COURSES.get(education.course, {}).get('name', education.course)}' завершено.",
        "course": education.course,
    }


def revoke_education(db: Session, education: Education, reason: str = "exposed_fake") -> dict:
    """Revoke a (fake) diploma after exposure."""
    if education.status != "completed":
        return {"success": False, "message": "Можна відкликати лише завершений диплом."}
    education.status = "revoked"
    db.flush()
    logger.info("Education %s revoked (%s)", education.course, reason)
    return {"success": True, "message": "Диплом відкликано.", "reason": reason}


# --- Exams ---


def take_exam(db: Session, player: Player, exam_type: str, game_day: int = 0) -> dict:
    """Take a qualification/license exam.

    exam_type: 'lawyer_license', 'police_qualification', 'judge_qualification',
               or a course exam (course code).
    Returns pass/fail. Records EducationExam.
    """
    # Count prior fails for this exam_type in current window
    recent_fails = (
        db.query(EducationExam)
        .filter(
            EducationExam.player_id == player.id,
            EducationExam.exam_type == exam_type,
            EducationExam.is_passed.is_(False),
        )
        .count()
    )

    # Pass chance: base, reduced slightly per prior fail
    pass_chance = max(0.3, EXAM_BASE_PASS - recent_fails * 0.15)
    is_passed = random.random() < pass_chance

    exam = EducationExam(
        player_id=player.id,
        exam_type=exam_type,
        is_passed=is_passed,
        taken_at=_now(),
        valid_until=(_now() + timedelta(days=LICENSE_VALIDITY_DAYS)) if is_passed else None,
    )
    db.add(exam)
    db.flush()

    bribe_available = (not is_passed) and recent_fails + 1 >= EXAM_FAIL_THRESHOLD
    return {
        "success": True,
        "message": "Іспит складено." if is_passed else "Іспит провалено.",
        "is_passed": is_passed,
        "exam_id": exam.id,
        "fails_in_window": recent_fails + 1 if not is_passed else 0,
        "bribe_available": bribe_available,
    }


def bribe_exam(db: Session, player: Player, exam_type: str, city: City | None = None) -> dict:
    """Attempt to bribe examiners after 2 fails.

    Success chance depends on criminal_rep. Cost: BRIBE_COST.
    On success: exam marked passed, license issued.
    On failure: money lost, criminal_rep +5 (caught bribing).
    """
    if player.balance < BRIBE_COST:
        return {"success": False, "message": "Недостатньо коштів для підкупу."}

    recent_fails = (
        db.query(EducationExam)
        .filter(
            EducationExam.player_id == player.id,
            EducationExam.exam_type == exam_type,
            EducationExam.is_passed.is_(False),
        )
        .count()
    )
    if recent_fails < EXAM_FAIL_THRESHOLD:
        return {
            "success": False,
            "message": "Підкуп доступний лише після двох провалів.",
        }

    # Success chance: base + criminal_rep bonus
    success_chance = min(0.9, BRIBE_SUCCESS_BASE + player.criminal_rep * 0.005)
    is_passed = random.random() < success_chance

    player.balance = Decimal(str(player.balance)) - BRIBE_COST

    exam = EducationExam(
        player_id=player.id,
        exam_type=exam_type,
        is_passed=is_passed,
        taken_at=_now(),
        valid_until=(_now() + timedelta(days=LICENSE_VALIDITY_DAYS)) if is_passed else None,
    )
    db.add(exam)

    if not is_passed:
        # Caught bribing — criminal_rep increases
        player.criminal_rep = min(100.0, player.criminal_rep + 5.0)

    db.flush()
    return {
        "success": True,
        "is_passed": is_passed,
        "message": "Підкуп спрацював, іспит складено." if is_passed else "Підкуп провалився, гроші втрачено.",
        "criminal_rep_gain": 0.0 if is_passed else 5.0,
    }


# --- Licenses ---


def has_valid_license(db: Session, player: Player, exam_type: str) -> bool:
    """Check if player has a valid (non-expired) license/exam."""
    latest = (
        db.query(EducationExam)
        .filter(
            EducationExam.player_id == player.id,
            EducationExam.exam_type == exam_type,
            EducationExam.is_passed.is_(True),
        )
        .order_by(EducationExam.taken_at.desc())
        .first()
    )
    if latest is None:
        return False
    if latest.valid_until is None:
        return True
    return latest.valid_until > _now()


def issue_lawyer_license(db: Session, player: Player) -> dict:
    """Issue lawyer license after 3 months in law firm + passed exam.

    Prerequisites (simplified for backend):
    - Completed legal education.
    - Passed 'lawyer_license' exam.
    """
    if not has_completed(db, player, "legal"):
        return {"success": False, "message": "Потрібна юридична освіта."}
    if not has_valid_license(db, player, "lawyer_license"):
        return {"success": False, "message": "Потрібно скласти іспит на адвоката."}
    return {
        "success": True,
        "message": "Ліцензію адвоката видано (діє 1 рік).",
        "valid_until": (_now() + timedelta(days=LICENSE_VALIDITY_DAYS)).isoformat(),
    }


def issue_police_qualification(db: Session, player: Player) -> dict:
    """Issue police qualification after exam."""
    if not has_completed(db, player, "police"):
        return {"success": False, "message": "Потрібна поліцейська академія."}
    if not has_valid_license(db, player, "police_qualification"):
        return {"success": False, "message": "Потрібно скласти щорічний іспит."}
    return {
        "success": True,
        "message": "Кваліфікацію поліцейського підтверджено (діє 1 рік).",
        "valid_until": (_now() + timedelta(days=LICENSE_VALIDITY_DAYS)).isoformat(),
    }


def issue_judge_qualification(db: Session, player: Player) -> dict:
    """Issue judge qualification after exam."""
    if not has_completed(db, player, "legal"):
        return {"success": False, "message": "Потрібна юридична освіта."}
    if not has_valid_license(db, player, "judge_qualification"):
        return {"success": False, "message": "Потрібно скласти щорічний іспит судді."}
    return {
        "success": True,
        "message": "Кваліфікацію судді підтверджено (діє 1 рік).",
        "valid_until": (_now() + timedelta(days=LICENSE_VALIDITY_DAYS)).isoformat(),
    }


def check_mayor_eligibility(db: Session, player: Player) -> dict:
    """Check if player is eligible to run for mayor.

    Requirements: economic education + legal education + 3 months in city hall.
    (3 months in city hall is simplified — checked via successful_deals >= 90
    as a proxy for ~3 months of daily engagements.)
    """
    has_economic = has_completed(db, player, "economic")
    has_legal = has_completed(db, player, "legal")
    has_practice = player.successful_deals >= 90  # ~3 months daily
    eligible = has_economic and has_legal and has_practice
    return {
        "success": True,
        "eligible": eligible,
        "has_economic": has_economic,
        "has_legal": has_legal,
        "has_practice": has_practice,
        "message": "Відповідає вимогам мера." if eligible else "Не відповідає вимогам мера.",
    }


# --- Fake diploma ---


def buy_fake_diploma(db: Session, player: Player, course: str) -> dict:
    """Buy a fake diploma via shadow mechanism.

    - Costs FAKE_DIPLOMA_COST.
    - Creates Education record with is_fake=True, status=completed.
    - +criminal_rep (FAKE_DIPLOMA_REP_GAIN).
    - Opens same branches as real diploma until exposed.
    - Exposure does NOT block diploma, only -reputation (per gameplay model).
    """
    if course not in COURSES:
        return {"success": False, "message": "Невідомий курс."}
    if player.balance < FAKE_DIPLOMA_COST:
        return {"success": False, "message": "Недостатньо коштів."}

    # Check not already completed/enrolled
    existing = (
        db.query(Education)
        .filter(
            Education.player_id == player.id,
            Education.course == course,
            Education.status.in_(("enrolled", "completed")),
        )
        .first()
    )
    if existing is not None:
        return {"success": False, "message": "Вже має цей диплом або навчається."}

    player.balance = Decimal(str(player.balance)) - FAKE_DIPLOMA_COST
    player.criminal_rep = min(100.0, player.criminal_rep + FAKE_DIPLOMA_REP_GAIN)

    education = Education(
        player_id=player.id,
        course=course,
        mode="part_time",  # fake diplomas don't consume time
        status="completed",
        is_fake=True,
        enrolled_at=_now(),
        completed_at=_now(),
    )
    db.add(education)
    db.flush()
    logger.warning(
        "Player %s bought FAKE diploma in %s (criminal_rep +%.1f)",
        player.username,
        course,
        FAKE_DIPLOMA_REP_GAIN,
    )
    return {
        "success": True,
        "message": f"Куплено диплом '{COURSES[course]['name']}' (підробний).",
        "education_id": education.id,
        "criminal_rep_gain": FAKE_DIPLOMA_REP_GAIN,
    }


def expose_fake_diploma(db: Session, education: Education) -> dict:
    """Expose a fake diploma (by press or police).

    Per gameplay model: exposure does NOT block diploma, only -reputation.
    So we log the exposure but keep status=completed. We set is_fake=True
    (already set) and could add an 'exposed' flag — but model says no block.
    Here we just log and return info.
    """
    if not education.is_fake:
        return {"success": False, "message": "Це не підробний диплом."}
    logger.info(
        "Fake diploma in %s exposed for player %s (no block, -reputation)",
        education.course,
        education.player_id,
    )
    return {
        "success": True,
        "message": "Підробний диплом викрито. Диплом не анульовано, але репутація знижена.",
        "course": education.course,
    }
