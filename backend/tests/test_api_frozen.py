import os

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.schemas.frozen import (
    FrozenSportsClubsResponse,
    FrozenSportsMatchesResponse,
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
        yield test_client
    app.dependency_overrides.clear()
    db.close()


def test_frozen_sports_simulate_matches_contract(client):
    response = client.post("/api/frozen/sports/simulate_matches")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["matches"]) == 3
    FrozenSportsMatchesResponse.model_validate(body)


def test_frozen_sports_clubs_contract(client):
    response = client.get("/api/frozen/sports/clubs")

    assert response.status_code == 200
    body = response.json()
    assert len(body["clubs"]) == 3
    assert body["clubs"][0]["owner"] == "ШІ-Управління"
    FrozenSportsClubsResponse.model_validate(body)


def test_mvp_sports_clubs_route_keeps_api_envelope(client):
    response = client.get("/api/sports/clubs")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert "clubs" in body["data"]
