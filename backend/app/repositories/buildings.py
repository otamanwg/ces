from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Building, BuildingApplication, LandParcel
from backend.app.repositories.base import BaseRepository


class BuildingRepository(BaseRepository[Building]):
    """Репозиторій для операцій з будівлями."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Building)

    def get_by_owner(self, player_id: UUID) -> list[Building]:
        """Отримати всі будівлі власника."""
        return self.db.query(Building).filter(Building.owner_player_id == player_id).all()

    def get_by_owner_with_details(self, player_id: UUID) -> list[Building]:
        """Отримати будівлі власника з деталями."""
        return (
            self.db.query(Building)
            .options(
                joinedload(Building.land_parcel),
                joinedload(Building.linked_business),
                joinedload(Building.blueprint),
            )
            .filter(Building.owner_player_id == player_id)
            .all()
        )

    def get_by_parcel(self, parcel_id: UUID) -> Building | None:
        """Отримати будівлю за ділянкою."""
        return self.db.query(Building).filter(Building.land_parcel_id == parcel_id).first()

    def get_active_in_city(self, city_id: UUID) -> list[Building]:
        """Отримати активні будівлі в місті."""
        return (
            self.db.query(Building)
            .join(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                Building.operating_status == "active",
            )
            .all()
        )

    def get_maintenance_due(self, city_id: UUID) -> list[Building]:
        """Отримати будівлі, що потребують ремонту."""
        return (
            self.db.query(Building)
            .join(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                Building.operating_status == "maintenance_due",
            )
            .all()
        )

    def create_from_application(self, application: BuildingApplication) -> Building:
        """Створити будівлю із заявки."""
        building = Building(
            land_parcel_id=application.land_parcel_id,
            owner_player_id=application.player_id,
            blueprint_id=application.business_blueprint_id,
            name=application.proposed_name,
            building_type=application.building_type,
            status="built",
            operating_status="inactive",
            created_at=datetime.utcnow(),
        )
        self.db.add(building)
        self.db.commit()
        self.db.refresh(building)
        return building

    def update_operating_status(self, building_id: UUID, status: str) -> bool:
        """Оновити операційний статус."""
        building = self.get_by_id(building_id)
        if building:
            building.operating_status = status
            if status == "active":
                building.activated_at = datetime.utcnow()
            elif status == "maintenance_due":
                building.maintenance_since = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def get_by_district(self, city_id: UUID, district_code: str) -> list[Building]:
        """Отримати будівлі в районі."""
        return (
            self.db.query(Building)
            .join(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                LandParcel.district_code == district_code,
            )
            .all()
        )

    def count_by_type_in_city(self, city_id: UUID, building_type: str) -> int:
        """Підрахувати будівлі певного типу в місті."""
        return (
            self.db.query(Building)
            .join(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                Building.building_type == building_type,
            )
            .count()
        )

    def get_with_business(self, building_id: UUID) -> Building | None:
        """Отримати будівлю з пов'язаним бізнесом."""
        return (
            self.db.query(Building)
            .options(joinedload(Building.linked_business))
            .filter(Building.id == building_id)
            .first()
        )


class BuildingApplicationRepository(BaseRepository[BuildingApplication]):
    """Репозиторій для будівельних заявок."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, BuildingApplication)

    def get_by_player(self, player_id: UUID) -> list[BuildingApplication]:
        """Отримати заявки гравця."""
        return (
            self.db.query(BuildingApplication)
            .filter(BuildingApplication.player_id == player_id)
            .order_by(BuildingApplication.created_at.desc())
            .all()
        )

    def get_pending_in_city(self, city_id: UUID) -> list[BuildingApplication]:
        """Отримати очікуючі заявки в місті."""
        return (
            self.db.query(BuildingApplication)
            .join(LandParcel)
            .filter(
                LandParcel.city_id == city_id,
                BuildingApplication.status == "pending",
            )
            .all()
        )

    def get_approved_for_player(self, player_id: UUID) -> list[BuildingApplication]:
        """Отримати схвалені заявки гравця."""
        return (
            self.db.query(BuildingApplication)
            .filter(
                BuildingApplication.player_id == player_id,
                BuildingApplication.status == "approved",
            )
            .all()
        )

    def create_application(self, player_id: UUID, parcel_id: UUID, blueprint_id: UUID, **kwargs) -> BuildingApplication:
        """Створити будівельну заявку."""
        application = BuildingApplication(
            player_id=player_id,
            land_parcel_id=parcel_id,
            business_blueprint_id=blueprint_id,
            status="pending",
            created_at=datetime.utcnow(),
            **kwargs,
        )
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def update_status(self, application_id: UUID, status: str, review_notes: str = None) -> bool:
        """Оновити статус заявки."""
        application = self.get_by_id(application_id)
        if application:
            application.status = status
            if status == "approved":
                application.approved_at = datetime.utcnow()
            elif status == "revision_required":
                application.revision_requested_at = datetime.utcnow()
            if review_notes:
                application.review_notes = review_notes
            self.db.commit()
            return True
        return False

    def mark_as_activated(self, application_id: UUID) -> bool:
        """Позначити заявку як активовану."""
        application = self.get_by_id(application_id)
        if application:
            application.status = "activated"
            application.activated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def get_with_details(self, application_id: UUID) -> BuildingApplication | None:
        """Отримати заявку з деталями."""
        return (
            self.db.query(BuildingApplication)
            .options(
                joinedload(BuildingApplication.land_parcel),
                joinedload(BuildingApplication.blueprint),
                joinedload(BuildingApplication.player),
            )
            .filter(BuildingApplication.id == application_id)
            .first()
        )
