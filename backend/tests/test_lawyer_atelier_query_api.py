"""API tests for Sprint 61 PR5 lawyer/atelier query endpoints.

Verifies GET /api/player/{id}/lawyer-engagements and atelier GET endpoints.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import Business, LawyerEngagement, Player, Skin
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
    register_res = test_client.post("/api/player/register", json={"username": "lawyer-tester"})
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


def test_player_lawyer_engagements_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/lawyer-engagements",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["engagements"] == []
    assert response["data"]["successful_deals"] == 0


def test_player_lawyer_engagements_after_create(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    # Create a second player as lawyer
    from backend.app.models import City

    city = db.query(City).first()
    lawyer = Player(username="test-lawyer", balance=Decimal("1000"), city_id=city.id)
    db.add(lawyer)
    db.commit()
    engagement = LawyerEngagement(
        lawyer_id=lawyer.id,
        client_id=player.id,
        deal_type="general",
        amount=Decimal("5000"),
        commission=Decimal("500"),
        success_chance_bonus=0.05,
    )
    db.add(engagement)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/lawyer-engagements",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    engagements = response["data"]["engagements"]
    assert len(engagements) == 1
    assert engagements[0]["deal_type"] == "general"
    assert engagements[0]["commission"] == 500.0
    assert engagements[0]["role"] == "client"


def test_atelier_player_skins_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/atelier/player-skins?player_id={player_id}",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["skins"] == []


def test_atelier_skins_for_atelier(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    from backend.app.models import City

    city = db.query(City).first()
    atelier = Business(
        city_id=city.id,
        owner_player_id=player.id,
        name="Fashion Atelier",
        type="atelier",
        status="active",
        cash_balance=Decimal("5000"),
    )
    db.add(atelier)
    db.commit()
    skin = Skin(
        designer_id=player.id,
        atelier_id=atelier.id,
        name="Cool Skin",
        config={"body": "slim"},
        rarity="rare",
        is_unique=False,
        copies_total=10,
        copies_sold=0,
        price=Decimal("300"),
    )
    db.add(skin)
    db.commit()

    response = test_client.get(
        f"/api/atelier/skins?atelier_id={atelier.id}",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    skins = response["data"]["skins"]
    assert len(skins) == 1
    assert skins[0]["name"] == "Cool Skin"
    assert skins[0]["rarity"] == "rare"
