from sqlalchemy.orm import Session

from backend.app.models import BusinessBlueprint
from backend.app.repositories.base import BaseRepository


class BusinessBlueprintRepository(BaseRepository[BusinessBlueprint]):
    """Репозиторій для операцій з бізнес-шаблонами."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, BusinessBlueprint)

    def get_all_active(self) -> list[BusinessBlueprint]:
        """Отримати всі активні шаблони."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(BusinessBlueprint.is_active)
            .order_by(
                BusinessBlueprint.risk_level,
                BusinessBlueprint.category,
                BusinessBlueprint.name,
            )
            .all()
        )

    def get_by_code(self, code: str) -> BusinessBlueprint | None:
        """Отримати шаблон за кодом."""
        return self.db.query(BusinessBlueprint).filter(BusinessBlueprint.code == code).first()
