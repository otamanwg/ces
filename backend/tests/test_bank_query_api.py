"""API tests for Sprint 61 bank query endpoints.

Verifies GET /api/banks, GET /api/player/{id}/deposits, GET /api/player/{id}/loans
return correct data shapes and respect auth.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import Business, City, Player
from backend.app.seed import seed_initial_data
from backend.app.services.bank_service import create_deposit, issue_loan
from backend.app.services.money import money
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

    # Seed doesn't create a bank business — create one for tests.
    city = db.query(City).first()
    bank = Business(
        city_id=city.id,
        name="TestBank",
        type="bank",
        legal_form="tov",
        cash_balance=Decimal("50000.00"),
        status="active",
    )
    db.add(bank)
    db.commit()

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
    register_res = test_client.post("/api/player/register", json={"username": "bank-tester"})
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


def _get_bank(db) -> Business:
    return db.query(Business).filter(Business.type == "bank").first()


def test_list_banks_returns_bank_list(client):
    test_client, db = client
    response = test_client.get("/api/banks").json()
    assert response["success"] is True
    banks = response["data"]["banks"]
    assert len(banks) > 0
    bank = banks[0]
    assert "id" in bank
    assert "name" in bank
    assert "cash_balance" in bank
    assert "status" in bank


def test_list_player_deposits_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/deposits",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["deposits"] == []


def test_list_player_deposits_after_deposit(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    player.balance = Decimal("5000.00")
    db.flush()
    bank = _get_bank(db)
    create_deposit(db, bank, player, money(500), money("5.00"), 0)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/deposits",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    deposits = response["data"]["deposits"]
    assert len(deposits) == 1
    assert deposits[0]["amount"] == 500.0
    assert deposits[0]["interest_rate"] == 5.0
    assert deposits[0]["is_active"] is True


def test_list_player_deposits_unauthorized(client):
    test_client, db = client
    response = test_client.get("/api/player/invalid-uuid/deposits").json()
    assert response["success"] is False


def test_list_player_loans_empty(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    response = test_client.get(
        f"/api/player/{player_id}/loans",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    assert response["data"]["loans"] == []


def test_list_player_loans_after_loan(client):
    test_client, db = client
    player_id, token = _register_and_complete_onboarding(test_client)
    player = db.query(Player).filter(Player.id == player_id).first()
    bank = _get_bank(db)
    issue_loan(db, bank, player, money(1000), money("12.00"), 30, 0)
    db.commit()

    response = test_client.get(
        f"/api/player/{player_id}/loans",
        headers={"X-Player-Token": token},
    ).json()
    assert response["success"] is True
    loans = response["data"]["loans"]
    assert len(loans) == 1
    assert loans[0]["principal_amount"] == 1000.0
    assert loans[0]["remaining_amount"] == 1000.0
    assert loans[0]["status"] == "active"
    assert loans[0]["due_game_day"] == 30
