from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import Business
from backend.app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    """Репозиторій для операцій з Business."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Business)

    def get_by_owner(self, owner_player_id: UUID) -> list[Business]:
        return self.db.query(Business).filter(Business.owner_player_id == owner_player_id).order_by(Business.name).all()

    def count_available_in_city(self, city_id: UUID) -> int:
        return (
            self.db.query(Business)
            .filter(
                Business.city_id == city_id,
                Business.owner_player_id.is_(None),
            )
            .count()
        )

    def count_buyable_in_city(self, city_id: UUID) -> int:
        return (
            self.db.query(Business)
            .filter(
                Business.city_id == city_id,
                Business.owner_player_id.is_(None),
                Business.type.in_(["shop", "factory", "private_hostel"]),
                Business.status == "active",
            )
            .count()
        )

    def count_owned_in_city(self, city_id: UUID) -> int:
        return (
            self.db.query(Business)
            .filter(
                Business.city_id == city_id,
                Business.owner_player_id.isnot(None),
            )
            .count()
        )
