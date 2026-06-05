from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import BuildingApplication, LandParcel, Player
from backend.app.services.business_blueprints import (
    blueprint_metric,
    get_business_blueprint,
    validate_blueprint_for_parcel,
)
from backend.app.services.land import calculate_player_city_land_share_pct
from backend.app.services.mayor_policy import BuildingProposal, evaluate_building_proposal


def create_building_application(
    db: Session,
    player: Player,
    land_parcel_id: UUID,
    business_blueprint_id: UUID | None = None,
    proposed_name: str = "",
    project_type: str = "",
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

    blueprint = None
    if business_blueprint_id is not None:
        blueprint = get_business_blueprint(db, business_blueprint_id)
        if not blueprint:
            return {"success": False, "message": "Бізнес-шаблон не знайдено."}

        blueprint_error = validate_blueprint_for_parcel(blueprint, parcel)
        if blueprint_error:
            return {"success": False, "message": blueprint_error}

    clean_name = proposed_name.strip()
    if not clean_name and blueprint:
        clean_name = blueprint.name
    if not clean_name:
        return {"success": False, "message": "Назва проєкту не може бути порожньою."}

    proposal_project_type = blueprint.project_type if blueprint else project_type.strip().lower()
    proposal_expected_jobs = blueprint_metric(blueprint, "expected_jobs", expected_jobs) if blueprint else max(0, expected_jobs)
    proposal_traffic_load = blueprint_metric(blueprint, "traffic_load", traffic_load) if blueprint else max(0, traffic_load)
    proposal_service_load = blueprint_metric(blueprint, "service_load", service_load) if blueprint else max(0, service_load)
    proposal_medical_load = blueprint_metric(blueprint, "medical_load", medical_load) if blueprint else max(0, medical_load)
    proposal_public_benefit = blueprint_metric(blueprint, "public_benefit", public_benefit) if blueprint else max(0, public_benefit)

    owner_share_pct = calculate_player_city_land_share_pct(db, player.city_id, player.id)
    proposal = BuildingProposal(
        project_type=proposal_project_type,
        land_area_hectares=Decimal(str(parcel.area_hectares)),
        expected_jobs=proposal_expected_jobs,
        traffic_load=proposal_traffic_load,
        service_load=proposal_service_load,
        medical_load=proposal_medical_load,
        public_benefit=proposal_public_benefit,
        owner_city_land_share_pct=owner_share_pct,
    )
    decision = evaluate_building_proposal(parcel.district, proposal)

    application = BuildingApplication(
        city_id=parcel.city_id,
        district_id=parcel.district_id,
        land_parcel_id=parcel.id,
        business_blueprint_id=blueprint.id if blueprint else None,
        applicant_player_id=player.id,
        proposed_name=clean_name,
        project_type=proposal_project_type,
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
