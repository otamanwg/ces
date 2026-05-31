from sqlalchemy.orm import Session

from backend.app.models import Hostel, Job, Player
from backend.app.services.ids import to_uuid
from backend.app.services.player_progress import build_goal_effects


def build_player_snapshot(db: Session, player: Player) -> dict:
    job = db.query(Job).filter(Job.filled_by_player_id == player.id).first()
    hostel = db.query(Hostel).filter(Hostel.tenant_player_id == player.id).first()

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
        "goal_effects": build_goal_effects(db, player),
    }


def get_player_snapshot(db: Session, player_id: str) -> dict | None:
    player = db.query(Player).filter(Player.id == to_uuid(player_id)).first()
    if not player:
        return None
    return build_player_snapshot(db, player)
