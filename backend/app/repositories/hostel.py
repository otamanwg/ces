from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import Hostel
from backend.app.repositories.base import BaseRepository


class HostelRepository(BaseRepository[Hostel]):
    """Репозиторій для операцій з Hostel."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Hostel)

    def get_by_tenant(self, player_id: UUID) -> Hostel | None:
        return self.db.query(Hostel).filter(Hostel.tenant_player_id == player_id).first()

    def get_first_free(self) -> Hostel | None:
        return (
            self.db.query(Hostel)
            .filter(Hostel.tenant_player_id.is_(None))
            .order_by(Hostel.rent_price_per_day, Hostel.room_number)
            .first()
        )
