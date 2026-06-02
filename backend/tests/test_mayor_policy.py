from decimal import Decimal

from backend.app.models import CityDistrict
from backend.app.services.mayor_policy import (
    APPROVED,
    REVISION_REQUIRED,
    BuildingProposal,
    evaluate_building_proposal,
)


def make_district(**overrides):
    values = {
        "code": "commercial_core",
        "name": "Комерційне ядро",
        "zone_type": "commercial",
        "description": "Test district",
        "display_order": 10,
        "land_available_hectares": Decimal("10.00"),
        "rent_level": 60,
        "job_supply": 70,
        "crime_risk": 25,
        "traffic": 50,
        "service_coverage": 65,
        "medical_coverage": 55,
        "land_value": 75,
        "desirability": 60,
    }
    values.update(overrides)
    return CityDistrict(**values)


def issue_codes(decision):
    return {issue.code for issue in decision.issues}


def test_ai_mayor_approves_small_commercial_project_in_matching_district():
    district = make_district()
    proposal = BuildingProposal(
        project_type="commercial",
        land_area_hectares=Decimal("1.50"),
        expected_jobs=12,
        traffic_load=8,
        service_load=10,
        medical_load=5,
        owner_city_land_share_pct=Decimal("4.00"),
    )

    decision = evaluate_building_proposal(district, proposal)

    assert decision.status == APPROVED
    assert decision.score == 100
    assert decision.issues == ()
    assert decision.questions == ()


def test_ai_mayor_requires_revision_for_residential_project_in_unsafe_industrial_district():
    district = make_district(
        code="industrial_edge",
        zone_type="industrial",
        land_available_hectares=Decimal("20.00"),
        crime_risk=48,
        service_coverage=45,
        medical_coverage=35,
        desirability=35,
    )
    proposal = BuildingProposal(
        project_type="residential",
        land_area_hectares=Decimal("3.00"),
        traffic_load=10,
        service_load=20,
        medical_load=12,
    )

    decision = evaluate_building_proposal(district, proposal)

    assert decision.status == REVISION_REQUIRED
    assert {
        "zoning_mismatch",
        "security_plan_required",
        "medical_access_required",
    }.issubset(issue_codes(decision))
    assert decision.score < 100
    assert len(decision.questions) == len(decision.issues)


def test_ai_mayor_flags_land_capacity_and_anti_monopoly_review():
    district = make_district(land_available_hectares=Decimal("2.00"))
    proposal = BuildingProposal(
        project_type="commercial",
        land_area_hectares=Decimal("5.00"),
        expected_jobs=5,
        owner_city_land_share_pct=Decimal("40.00"),
    )

    decision = evaluate_building_proposal(district, proposal)

    assert decision.status == REVISION_REQUIRED
    assert {"land_capacity", "anti_monopoly_review"}.issubset(issue_codes(decision))


def test_ai_mayor_requires_transport_plan_for_overloaded_project():
    district = make_district(traffic=80)
    proposal = BuildingProposal(
        project_type="commercial",
        land_area_hectares=Decimal("1.00"),
        expected_jobs=8,
        traffic_load=10,
    )

    decision = evaluate_building_proposal(district, proposal)

    assert decision.status == REVISION_REQUIRED
    assert "traffic_plan_required" in issue_codes(decision)


def test_ai_mayor_allows_civic_project_through_anti_monopoly_gate():
    district = make_district(zone_type="suburban", service_coverage=45)
    proposal = BuildingProposal(
        project_type="civic",
        land_area_hectares=Decimal("1.00"),
        service_load=5,
        owner_city_land_share_pct=Decimal("60.00"),
        public_benefit=80,
    )

    decision = evaluate_building_proposal(district, proposal)

    assert "anti_monopoly_review" not in issue_codes(decision)
