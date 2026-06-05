from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import Building, BuildingApplication, Player


BUILT = "built"
INACTIVE = "inactive"
APPLICATION_ACTIVATED = "activated"
PARCEL_BUILT = "built"


def activate_building_application(db: Session, player: Player, application_id: UUID) -> dict:
    application = (
        db.query(BuildingApplication)
        .filter(BuildingApplication.id == application_id)
        .with_for_update()
        .first()
    )
    if not application or application.city_id != player.city_id:
        return {"success": False, "message": "Будівельну заявку не знайдено."}

    if application.applicant_player_id != player.id:
        return {"success": False, "message": "Активувати можна лише власну будівельну заявку."}

    if application.status == APPLICATION_ACTIVATED:
        return {"success": False, "message": "Цю будівельну заявку вже активовано."}

    if application.status != "approved":
        return {"success": False, "message": "Активувати можна лише погоджену AI-мером заявку."}

    parcel = application.land_parcel
    if parcel.owner_player_id != player.id or parcel.status != "owned":
        return {"success": False, "message": "Ділянка має бути у власності заявника і без готової будівлі."}

    existing_building = (
        db.query(Building)
        .filter(
            (Building.land_parcel_id == parcel.id)
            | (Building.source_application_id == application.id)
        )
        .first()
    )
    if existing_building:
        return {"success": False, "message": "Для цієї ділянки або заявки вже існує будівля."}

    building = Building(
        city_id=application.city_id,
        district_id=application.district_id,
        land_parcel_id=application.land_parcel_id,
        source_application_id=application.id,
        owner_player_id=player.id,
        name=application.proposed_name,
        project_type=application.project_type,
        status=BUILT,
        operating_status=INACTIVE,
    )
    db.add(building)
    application.status = APPLICATION_ACTIVATED
    parcel.status = PARCEL_BUILT
    db.commit()
    db.refresh(building)

    return {
        "success": True,
        "message": f"Будівлю '{building.name}' створено як міський актив.",
        "building": building,
    }
