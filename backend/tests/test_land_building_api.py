import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import BuildingApplication, LandParcel, Player
from backend.app.schemas.mvp import BuildingApplicationData, LandParcelsData
from backend.app.seed import seed_initial_data
from backend.app.services.land import OWNED
from backend.main import app
from backend.tests.db import make_test_session


TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")
os.environ["CITY_SKIP_DB_INIT"] = "true"

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


@pytest.fixture
def client():
    db = make_test_session(TEST_DATABASE_URL)
    seed_initial_data(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, db
    app.dependency_overrides.clear()
    db.close()


def register_player(test_client, username: str):
    body = test_client.post("/api/player/register", json={"username": username}).json()
    assert body["success"] is True
    return body["data"]["id"], body["data"]["auth_token"]


def test_land_parcels_endpoint_returns_seeded_city_land(client):
    test_client, _db = client

    res = test_client.get("/api/land/parcels")

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = LandParcelsData.model_validate(body["data"])
    parcels = [parcel.model_dump() for parcel in data.parcels]
    assert len(parcels) == 6
    assert parcels[0]["code"] == "bus_station_kiosk_lot"
    assert parcels[0]["district_code"] == "bus_station"
    assert parcels[0]["current_price"] == 200.0
    assert parcels[-1]["code"] == "outer_expansion_lot"
    assert parcels[-1]["land_type"] == "near_city"


def test_building_application_requires_owned_land(client):
    test_client, _db = client
    player_id, token = register_player(test_client, "landless-builder")
    parcel = test_client.get("/api/land/parcels").json()["data"]["parcels"][0]

    res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": parcel["id"],
            "proposed_name": "Кіоск біля вокзалу",
            "project_type": "commercial",
            "expected_jobs": 2,
        },
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["message"] == "Будівельну заявку можна подати лише на власну ділянку."


def test_building_application_uses_ai_mayor_policy_and_is_idempotent(client):
    test_client, db = client
    player_id, token = register_player(test_client, "parcel-owner")
    player = db.query(Player).filter(Player.id == player_id).one()
    parcel = db.query(LandParcel).filter(LandParcel.code == "commercial_core_small_lot").one()
    parcel.owner_player_id = player.id
    parcel.status = OWNED
    db.commit()

    payload = {
        "player_id": player_id,
        "land_parcel_id": str(parcel.id),
        "proposed_name": "Малий торговий центр",
        "project_type": "commercial",
        "expected_jobs": 12,
        "traffic_load": 5,
        "service_load": 8,
        "medical_load": 2,
        "public_benefit": 20,
    }
    headers = {"X-Player-Token": token, "Idempotency-Key": "building-application-1"}
    res = test_client.post("/api/building/applications", json=payload, headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingApplicationData.model_validate(body["data"])
    assert data.status == "approved"
    assert data.mayor_score == 100
    assert data.mayor_issues == []
    assert Decimal(str(data.land_area_hectares)) == Decimal("0.5")
    assert db.query(BuildingApplication).count() == 1

    repeat = test_client.post("/api/building/applications", json=payload, headers=headers)
    assert repeat.status_code == 200
    assert repeat.json() == body
    assert db.query(BuildingApplication).count() == 1


def test_building_application_can_return_revision_questions(client):
    test_client, db = client
    player_id, token = register_player(test_client, "suburb-industrialist")
    player = db.query(Player).filter(Player.id == player_id).one()
    parcel = db.query(LandParcel).filter(LandParcel.code == "suburban_home_lot").one()
    parcel.owner_player_id = player.id
    parcel.status = OWNED
    db.commit()

    res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "proposed_name": "Цех біля приватного сектору",
            "project_type": "industrial",
            "expected_jobs": 6,
            "traffic_load": 20,
            "service_load": 10,
        },
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingApplicationData.model_validate(body["data"])
    assert data.status == "revision_required"
    assert "zoning_mismatch" in {issue.code for issue in data.mayor_issues}
    assert len(data.mayor_questions) >= 1
