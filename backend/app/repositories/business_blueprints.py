from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import Building, BuildingApplication, BusinessBlueprint
from backend.app.repositories.base import BaseRepository


class BusinessBlueprintRepository(BaseRepository[BusinessBlueprint]):
    """Репозиторій для операцій з бізнес-шаблонами."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, BusinessBlueprint)

    def get_all_active(self) -> list[BusinessBlueprint]:
        """Отримати всі активні шаблони."""
        return (
            self.db.query(BusinessBlueprint).filter(BusinessBlueprint.is_active).order_by(BusinessBlueprint.code).all()
        )

    def get_by_code(self, code: str) -> BusinessBlueprint | None:
        """Отримати шаблон за кодом."""
        return self.db.query(BusinessBlueprint).filter(BusinessBlueprint.code == code).first()

    def get_by_category(self, category: str) -> list[BusinessBlueprint]:
        """Отримати шаблони за категорією."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.category == category,
                BusinessBlueprint.is_active,
            )
            .order_by(BusinessBlueprint.opening_fee)
            .all()
        )

    def get_by_zoning(self, allowed_zoning: str) -> list[BusinessBlueprint]:
        """Отримати шаблони, дозволені для певної зони."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.allowed_zoning.contains(allowed_zoning),
                BusinessBlueprint.is_active,
            )
            .all()
        )

    def get_for_land_type(self, land_type: str) -> list[BusinessBlueprint]:
        """Отримати шаблони для типу землі."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.allowed_land_types.contains(land_type),
                BusinessBlueprint.is_active,
            )
            .all()
        )

    def get_affordable_for_player(self, player_id: UUID, player_balance: int) -> list[BusinessBlueprint]:
        """Отримати шаблони, які гравець може дозволити собі."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.is_active,
                BusinessBlueprint.opening_fee <= player_balance,
            )
            .order_by(BusinessBlueprint.opening_fee)
            .all()
        )

    def get_with_applications_count(self, blueprint_id: UUID) -> BusinessBlueprint | None:
        """Отримати шаблон з кількістю заявок."""
        from sqlalchemy import func

        subquery = (
            self.db.query(func.count(BuildingApplication.id))
            .filter(BuildingApplication.business_blueprint_id == blueprint_id)
            .subquery()
        )

        return (
            self.db.query(BusinessBlueprint)
            .add_columns(subquery.label("applications_count"))
            .filter(BusinessBlueprint.id == blueprint_id)
            .first()
        )

    def get_with_buildings_count(self, blueprint_id: UUID) -> BusinessBlueprint | None:
        """Отримати шаблон з кількістю побудованих будівель."""
        from sqlalchemy import func

        subquery = self.db.query(func.count(Building.id)).filter(Building.blueprint_id == blueprint_id).subquery()

        return (
            self.db.query(BusinessBlueprint)
            .add_columns(subquery.label("buildings_count"))
            .filter(BusinessBlueprint.id == blueprint_id)
            .first()
        )

    def search_by_name_or_description(self, query: str) -> list[BusinessBlueprint]:
        """Пошук шаблонів за назвою або описом."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.is_active,
                (BusinessBlueprint.name.ilike(f"%{query}%") | BusinessBlueprint.description.ilike(f"%{query}%")),
            )
            .order_by(BusinessBlueprint.name)
            .all()
        )

    def get_by_complexity(self, min_complexity: int, max_complexity: int) -> list[BusinessBlueprint]:
        """Отримати шаблони за складністю."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.is_active,
                BusinessBlueprint.complexity >= min_complexity,
                BusinessBlueprint.complexity <= max_complexity,
            )
            .order_by(BusinessBlueprint.complexity)
            .all()
        )

    def get_by_project_type(self, project_type: str) -> list[BusinessBlueprint]:
        """Отримати шаблони за типом проєкту."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.project_type == project_type,
                BusinessBlueprint.is_active,
            )
            .all()
        )

    def create_blueprint(self, **kwargs) -> BusinessBlueprint:
        """Створити новий шаблон."""
        blueprint = BusinessBlueprint(**kwargs)
        self.db.add(blueprint)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def update_blueprint(self, blueprint_id: UUID, **kwargs) -> bool:
        """Оновити шаблон."""
        blueprint = self.get_by_id(blueprint_id)
        if blueprint:
            for key, value in kwargs.items():
                if hasattr(blueprint, key):
                    setattr(blueprint, key, value)
            self.db.commit()
            return True
        return False

    def deactivate_blueprint(self, blueprint_id: UUID) -> bool:
        """Деактивувати шаблон."""
        blueprint = self.get_by_id(blueprint_id)
        if blueprint:
            blueprint.is_active = False
            self.db.commit()
            return True
        return False

    def get_stats_summary(self) -> dict:
        """Отримати статистичну звітність по шаблонах."""
        from sqlalchemy import func

        result = (
            self.db.query(
                BusinessBlueprint.category,
                func.count(BusinessBlueprint.id).label("count"),
                func.avg(BusinessBlueprint.opening_fee).label("avg_fee"),
                func.avg(BusinessBlueprint.complexity).label("avg_complexity"),
            )
            .filter(BusinessBlueprint.is_active)
            .group_by(BusinessBlueprint.category)
            .all()
        )

        return [
            {
                "category": row.category,
                "count": row.count,
                "avg_fee": float(row.avg_fee) if row.avg_fee else 0,
                "avg_complexity": float(row.avg_complexity) if row.avg_complexity else 0,
            }
            for row in result
        ]

    def get_for_visual_pack(self, visual_pack: str) -> list[BusinessBlueprint]:
        """Отримати шаблони для візуального паку."""
        return (
            self.db.query(BusinessBlueprint)
            .filter(
                BusinessBlueprint.is_active,
                BusinessBlueprint.visual_style_pack == visual_pack,
            )
            .all()
        )
