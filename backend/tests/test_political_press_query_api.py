"""API tests for Sprint 61 PR3 political/press query endpoints.

Verifies GET /api/player/{id}/city-office, /press-investigations, /press-blackmails
return correct data shapes and respect auth.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import (
    City,
    CityOffice,
    Player,
    PressBlackmail,
    PressInvestigation,
)
from backend.app.seed import seed_initial_data
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
    register_res = test_client.post("/api/player/register", json={"username": "pol-tester"})
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


def test_player_city_office_no_office(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/city-office",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["office"] is None
    assert response["data"]["is_mayor"] is False


def test_player_city_office_after_hire(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    city = db.query(City).first()
    office = CityOffice(
        city_id=city.id,
        player_id=player.id,
        position="worker",
        department="economy",
        hired_at_game_day=0,
        is_active=True,
    )
    db.add(office)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/city-office",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    office_data = response["data"]["office"]
    assert office_data is not None
    assert office_data["position"] == "worker"
    assert office_data["department"] == "economy"
    assert office_data["is_active"] is True


def test_player_press_investigations_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/press-investigations",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["investigations"] == []


def test_player_press_investigations_after_create(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    city = db.query(City).first()
    # Create a second player as target
    target = Player(username="press-target", balance=Decimal("1000"), city_id=city.id)
    db.add(target)
    db.commit()
    investigation = PressInvestigation(
        target_player_id=target.id,
        journalist_id=player.id,
        incident_type="corruption",
        press_evidence=0.5,
        scale="local",
    )
    db.add(investigation)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/press-investigations",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    investigations = response["data"]["investigations"]
    assert len(investigations) == 1
    assert investigations[0]["incident_type"] == "corruption"
    assert investigations[0]["press_evidence"] == 0.5
    assert investigations[0]["is_published"] is False


def test_player_press_blackmails_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/press-blackmails",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["blackmails"] == []


def test_player_press_blackmails_after_create(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    city = db.query(City).first()
    journalist = Player(username="press-journalist", balance=Decimal("1000"), city_id=city.id)
    db.add(journalist)
    db.commit()
    blackmail = PressBlackmail(
        journalist_id=journalist.id,
        target_id=player.id,
        amount_demanded=Decimal("500.00"),
        status="pending",
    )
    db.add(blackmail)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/press-blackmails",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    blackmails = response["data"]["blackmails"]
    assert len(blackmails) == 1
    assert blackmails[0]["amount_demanded"] == 500.0
    assert blackmails[0]["status"] == "pending"
