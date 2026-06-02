from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import BuildingApplication, LandParcel, Player
from backend.app.services.land import calculate_player_city_land_share_pct
from backend.app.services.mayor_policy import BuildingProposal, evaluate_building_proposal


def create_building_application(
    db: Session,
    player: Player,
    land_parcel_id: UUID,
    proposed_name: str,
    project_type: str,
    expected_jobs: int = 0,
    traffic_load: int = 0,
    service_load: int = 0,
    medical_load: int = 0,
    public_benefit: int = 0,
) -> dict:
    parcel = db.query(LandParcel).filter(LandParcel.id == land_parcel_id).first()
    if not parcel or parcel.city_id != player.city_id:
        return {"success": False, "message": "Ділянку не знайдено."}

    if parcel.owner_player_id != player.id or parcel.status != "owned":
        return {"success": False, "message": "Будівельну заявку можна подати лише на власну ділянку."}

    clean_name = proposed_name.strip()
    if not clean_name:
        return {"success": False, "message": "Назва проєкту не може бути порожньою."}

    owner_share_pct = calculate_player_city_land_share_pct(db, player.city_id, player.id)
    proposal = BuildingProposal(
        project_type=project_type,
        land_area_hectares=Decimal(str(parcel.area_hectares)),
        expected_jobs=max(0, expected_jobs),
        traffic_load=max(0, traffic_load),
        service_load=max(0, service_load),
        medical_load=max(0, medical_load),
        public_benefit=max(0, public_benefit),
        owner_city_land_share_pct=owner_share_pct,
    )
    decision = evaluate_building_proposal(parcel.district, proposal)

    application = BuildingApplication(
        city_id=parcel.city_id,
        district_id=parcel.district_id,
        land_parcel_id=parcel.id,
        applicant_player_id=player.id,
        proposed_name=clean_name,
        project_type=project_type.strip().lower(),
        land_area_hectares=parcel.area_hectares,
        expected_jobs=proposal.expected_jobs,
        traffic_load=proposal.traffic_load,
        service_load=proposal.service_load,
        medical_load=proposal.medical_load,
        public_benefit=proposal.public_benefit,
        status=decision.status,
        mayor_score=decision.score,
        mayor_summary=decision.summary,
        mayor_issues=[{"code": issue.code, "message": issue.message} for issue in decision.issues],
        mayor_questions=list(decision.questions),
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": decision.summary,
        "application": application,
    }
