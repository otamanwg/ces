from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Hostel, Job, Player
from backend.app.services.education import load_manager_exam
from backend.app.services.ids import to_uuid
from backend.app.services.money import money
from backend.app.services.player_progress import build_goal_effects


def _education_rank(value: str) -> int:
    return {"High School": 1, "College": 2, "University": 3}.get(value, 1)


def build_player_actions(db: Session, player: Player, job: Job | None, hostel: Hostel | None) -> dict:
    exam = load_manager_exam()
    exam_cost = money(exam.get("cost_to_take", 100)) if exam else Decimal("100.00")
    player_rank = _education_rank(player.education_level)

    eligible_vacancy = (
        db.query(Job)
        .filter(
            Job.filled_by_player_id.is_(None),
        )
        .all()
    )
    has_eligible_vacancy = any(_education_rank(vacancy.min_education) <= player_rank for vacancy in eligible_vacancy)

    return {
        "can_apply_job": has_eligible_vacancy,
        "can_work": bool(job and player.energy >= job.energy_cost_per_shift),
        "can_sleep": hostel is not None,
        "can_take_exam": player.education_level == "High School" and money(player.balance) >= exam_cost,
    }


def build_player_snapshot(db: Session, player: Player) -> dict:
    job = db.query(Job).filter(Job.filled_by_player_id == player.id).first()
    hostel = db.query(Hostel).filter(Hostel.tenant_player_id == player.id).first()
    actions = build_player_actions(db, player, job, hostel)

    return {
        "id": str(player.id),
        "username": player.username,
        "balance": float(player.balance),
        "energy": player.energy,
        "mood": player.mood,
        "education_level": player.education_level,
        "diploma_verified": player.diploma_verified,
        "job": job.title if job else "Безробітний",
        "job_id": str(job.id) if job else None,
        "hostel": f"Кімната №{hostel.room_number} (Хостел)" if hostel else "На вулиці",
        "actions": actions,
        "goal_effects": build_goal_effects(db, player),
    }


def get_player_snapshot(db: Session, player_id: str) -> dict | None:
    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    if not player:
        return None
    return build_player_snapshot(db, player)
