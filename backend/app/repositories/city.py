from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import City
from backend.app.repositories.base import BaseRepository


class CityRepository(BaseRepository[City]):
    """Репозиторій для операцій з City."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, City)

    def get_first(self) -> City | None:
        return self.db.query(City).first()
