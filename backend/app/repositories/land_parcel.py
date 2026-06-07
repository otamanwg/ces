from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import CityDistrict, LandParcel
from backend.app.repositories.base import BaseRepository


class LandParcelRepository(BaseRepository[LandParcel]):
    """Репозиторій для операцій з LandParcel."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, LandParcel)

    def list_by_city(self, city_id: UUID) -> list[LandParcel]:
        return (
            self.db.query(LandParcel)
            .join(CityDistrict, CityDistrict.id == LandParcel.district_id)
            .filter(LandParcel.city_id == city_id)
            .order_by(
                CityDistrict.display_order, LandParcel.current_price, LandParcel.label
            )
            .all()
        )

    def list_by_city_and_owner(
        self, city_id: UUID, owner_player_id: UUID
    ) -> list[LandParcel]:
        return (
            self.db.query(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                LandParcel.owner_player_id == owner_player_id,
            )
            .all()
        )

    def get_city_total_area(self, city_id: UUID) -> float:
        from sqlalchemy import func

        result = (
            self.db.query(func.sum(LandParcel.area_hectares))
            .filter(LandParcel.city_id == city_id)
            .scalar()
        )
        return float(result) if result else 0.0
