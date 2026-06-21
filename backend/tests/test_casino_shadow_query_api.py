"""API tests for Sprint 61 PR4 casino/shadow query + shadow market endpoints.

Verifies GET /api/player/{id}/shadow-businesses, /casino-games,
POST /api/shadow/market/buy, /market/sell, /fraud-refuse.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import Business, CasinoGame, City, Player, ShadowBusiness
from backend.app.seed import seed_initial_data
from backend.app.services.shadow_service import add_criminal_rep
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
    register_res = test_client.post("/api/player/register", json={"username": "casino-tester"})
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


def test_player_shadow_businesses_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/shadow-businesses",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["businesses"] == []
    assert response["data"]["criminal_rep"] == 0.0


def test_player_shadow_businesses_after_create(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    city = db.query(City).first()
    # Need a district
    from backend.app.models import CityDistrict

    district = db.query(CityDistrict).first()
    if not district:
        district = CityDistrict(city_id=city.id, name="TestDistrict", desirability=50)
        db.add(district)
        db.commit()
    # Give player criminal_rep
    add_criminal_rep(db, player, 50.0, "test")
    db.commit()
    biz = ShadowBusiness(
        owner_id=player.id,
        type="illegal_bar",
        district_id=district.id,
        cash_balance=Decimal("150.00"),
    )
    db.add(biz)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/shadow-businesses",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    businesses = response["data"]["businesses"]
    assert len(businesses) == 1
    assert businesses[0]["type"] == "illegal_bar"
    assert businesses[0]["cash_balance"] == 150.0
    assert businesses[0]["is_discovered"] is False
    assert response["data"]["criminal_rep"] >= 50.0


def test_player_casino_games_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/casino-games",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["casinos"] == []
    assert response["data"]["games"] == []


def test_player_casino_games_after_create(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    city = db.query(City).first()
    casino = Business(
        city_id=city.id,
        owner_player_id=player.id,
        name="Lucky Casino",
        type="casino",
        status="active",
        cash_balance=Decimal("10000"),
        daily_revenue=Decimal("500"),
    )
    db.add(casino)
    db.commit()
    game = CasinoGame(
        casino_business_id=casino.id,
        game_type="poker",
        status="waiting",
        players=[],
        pot=Decimal("0"),
        rake=Decimal("0"),
    )
    db.add(game)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/casino-games",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert len(response["data"]["casinos"]) == 1
    assert response["data"]["casinos"][0]["name"] == "Lucky Casino"
    assert len(response["data"]["games"]) == 1
    assert response["data"]["games"][0]["game_type"] == "poker"
    assert response["data"]["games"][0]["status"] == "waiting"


def test_shadow_market_buy_requires_rep(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.post(
        "/api/shadow/market/buy",
        json={"player_id": player_id, "item_type": "alcohol", "quantity": 1},
    ).json()
    assert response["success"] is False


def test_shadow_market_buy_with_rep(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    add_criminal_rep(db, player, 50.0, "test")
    db.commit()
    response = test_client.post(
        "/api/shadow/market/buy",
        json={"player_id": player_id, "item_type": "alcohol", "quantity": 1},
    ).json()
    assert response["success"] is True


def test_shadow_market_sell_with_rep(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    add_criminal_rep(db, player, 50.0, "test")
    db.commit()
    response = test_client.post(
        "/api/shadow/market/sell",
        json={"player_id": player_id, "item_type": "tobacco", "quantity": 2},
    ).json()
    assert response["success"] is True


def test_shadow_fraud_refuse(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.post(
        "/api/shadow/fraud-refuse",
        json={"player_id": player_id},
    ).json()
    assert response["success"] is True
