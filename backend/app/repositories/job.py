from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import Job
from backend.app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Репозиторій для операцій з Job."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Job)

    def get_vacant(self) -> list[Job]:
        return self.db.query(Job).filter(Job.filled_by_player_id.is_(None)).all()

    def get_active_for_player(self, player_id: UUID) -> Job | None:
        return self.db.query(Job).filter(Job.filled_by_player_id == player_id).first()

    def get_first_vacant_by_min_education(self, min_education: str) -> Job | None:
        return self.db.query(Job).filter(Job.min_education == min_education, Job.filled_by_player_id.is_(None)).first()
