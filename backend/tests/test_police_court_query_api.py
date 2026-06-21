"""API tests for Sprint 61 PR2 police/court query endpoints.

Verifies GET /api/police/officer, GET /api/player/{id}/police-records,
GET /api/player/{id}/court-cases return correct data shapes and respect auth.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import City, CourtCase, Player, PoliceRecord
from backend.app.seed import seed_initial_data
from backend.app.services.police_service import hire_police_officer
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


def _register_and_complete_onboarding(test_client):
    register_res = test_client.post("/api/player/register", json={"username": "police-tester"})
    assert register_res.status_code == 200
    body = register_res.json()
    player_id = body["data"]["id"]
    token = body["data"]["auth_token"]
    test_client.post(
        "/api/player/onboarding/choose",
        json={"player_id": player_id, "choice": "find_housing"},
        headers={"X-Player-Token": token},
    )
    return player_id, token


def test_police_officer_status_no_officer(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/police/officer?player_id={player_id}",
    ).json()
    assert response["success"] is True
    assert response["data"]["officer"] is None


def test_police_officer_status_after_hire(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    city = db.query(City).first()
    player = db.query(Player).filter(Player.id == player_id).first()
    hire_police_officer(db, city, player, 0)
    db.commit()

    response = test_client.get(
        f"/api/police/officer?player_id={player_id}",
    ).json()
    assert response["success"] is True
    officer = response["data"]["officer"]
    assert officer is not None
    assert officer["rank"] == "patrol"
    assert officer["is_active"] is True
    assert officer["successful_investigations"] == 0


def test_player_police_records_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/police-records",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["records"] == []


def test_player_police_records_after_record(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    record = PoliceRecord(
        player_id=player.id,
        offense_type="minor_offense",
        fine_amount=Decimal("100.00"),
        status="fined",
    )
    db.add(record)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/police-records",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    records = response["data"]["records"]
    assert len(records) == 1
    assert records[0]["offense_type"] == "minor_offense"
    assert records[0]["fine_amount"] == 100.0
    assert records[0]["status"] == "fined"


def test_player_court_cases_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/court-cases",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["cases"] == []


def test_player_court_cases_after_case(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    case = CourtCase(
        defendant_id=player.id,
        verdict="fine",
        is_appealed=False,
    )
    db.add(case)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/court-cases",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    cases = response["data"]["cases"]
    assert len(cases) == 1
    assert cases[0]["verdict"] == "fine"
    assert cases[0]["is_appealed"] is False
