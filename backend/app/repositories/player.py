from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Hostel, Player
from backend.app.repositories.base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    """Репозиторій для операцій з Player."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Player)

    def get_by_auth_token(self, player_id: UUID, player_token: str) -> Player | None:
        return (
            self.db.query(Player)
            .filter(Player.id == player_id, Player.auth_token == player_token)
            .first()
        )

    def list_by_city(self, city_id: UUID) -> list[Player]:
        return self.db.query(Player).filter(Player.city_id == city_id).all()

    def list_by_city_with_hostel(self, city_id: UUID) -> list[Player]:
        return (
            self.db.query(Player)
            .options(joinedload(Player.hostel_rented))
            .filter(Player.city_id == city_id)
            .all()
        )

    def count_hungry_in_city(self, city_id: UUID, threshold: int = 70) -> int:
        from sqlalchemy import func

        return (
            self.db.query(func.count(Player.id))
            .filter(Player.city_id == city_id, Player.hunger >= threshold)
            .scalar()
        )

    def count_homeless_in_city(self, city_id: UUID) -> int:
        return (
            self.db.query(Player)
            .outerjoin(Hostel, Hostel.tenant_player_id == Player.id)
            .filter(Player.city_id == city_id, Hostel.id.is_(None))
            .count()
        )
