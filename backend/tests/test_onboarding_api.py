import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend.app.core.tokens import hash_player_token
from backend.app.database import get_db
from backend.app.models import (
    City,
    Player,
    PlayerAvatar,
    PlayerOnboarding,
    PoliceRecord,
    TransactionModelLog,
)
from backend.app.schemas.mvp import AvatarCatalogData, PlayerSnapshotData
from backend.app.seed import seed_initial_data
from backend.app.services.onboarding import (
    ARRIVAL_CHOICE,
    COMPLETED,
    FIND_HOUSING,
    HOUSING_SEARCH,
    ONBOARDING_REQUIRED_MESSAGE,
    POLICE_PENDING,
    POLICE_RECOVERED,
    REPORT_TO_POLICE,
)
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


def register_player(test_client: TestClient, username: str) -> tuple[dict, dict]:
    body = test_client.post("/api/player/register", json={"username": username}).json()
    assert body["success"] is True
    headers = {"X-Player-Token": body["data"]["auth_token"]}
    return body, headers


def choose_path(
    test_client: TestClient,
    player_id: str,
    headers: dict,
    choice: str,
    key: str,
) -> dict:
    return test_client.post(
        "/api/player/onboarding/choose",
        json={"player_id": player_id, "choice": choice},
        headers={**headers, "Idempotency-Key": key},
    ).json()


def test_registration_starts_arrival_and_blocks_ordinary_actions(client):
    test_client, _db = client
    register, headers = register_player(test_client, "new-arrival")
    data = register["data"]

    assert 300 <= data["balance"] <= 400
    assert data["hostel"] == "На вулиці"
    assert data["onboarding"]["stage"] == ARRIVAL_CHOICE
    assert data["onboarding"]["completed"] is False
    assert data["tutorial_age_group"] == "adult"
    assert data["avatar"]["body_preset_code"] == "body_standard"
    assert data["avatar"]["face_preset_code"] == "face_01"
    assert data["avatar"]["animation_profile_code"] == "humanoid_context_v1"
    assert data["avatar"]["equipped_outfit"]["upper"] == "upper_stock_jacket"
    assert data["avatar"]["fashion_score"] == 8
    assert data["onboarding"]["police_recovery_claimable"] is False
    assert data["onboarding"]["available_choices"] == [REPORT_TO_POLICE, FIND_HOUSING]
    assert all(available is False for available in data["actions"].values())
    PlayerSnapshotData.model_validate(data)

    vacancy = test_client.get("/api/jobs/vacancies").json()["data"]["vacancies"][0]
    blocked = test_client.post(
        "/api/jobs/apply",
        json={"player_id": data["id"], "job_id": vacancy["id"]},
        headers=headers,
    ).json()

    assert blocked["success"] is False
    assert blocked["message"] == ONBOARDING_REQUIRED_MESSAGE
    assert blocked["data"]["onboarding"]["stage"] == ARRIVAL_CHOICE


def test_registration_accepts_supported_tutorial_age_group(client):
    test_client, db = client
    response = test_client.post(
        "/api/player/register",
        json={"username": "teen-arrival", "tutorial_age_group": "teen"},
    )
    body = response.json()

    assert body["success"] is True
    assert body["data"]["tutorial_age_group"] == "teen"
    player = db.query(Player).filter(Player.id == body["data"]["id"]).one()
    assert player.tutorial_age_group == "teen"
    PlayerSnapshotData.model_validate(body["data"])


def test_registration_accepts_avatar_identity(client):
    test_client, db = client
    response = test_client.post(
        "/api/player/register",
        json={
            "username": "avatar-owner",
            "avatar": {
                "body_preset_code": "body_sturdy",
                "face_preset_code": "face_20",
                "skin_tone_code": "skin_06",
                "hair_style_code": "hair_long_02",
                "hair_color_code": "hair_auburn",
            },
        },
    )
    body = response.json()

    assert body["success"] is True
    assert body["data"]["avatar"]["body_preset_code"] == "body_sturdy"
    assert body["data"]["avatar"]["face_preset_code"] == "face_20"
    assert body["data"]["avatar"]["hair_style_code"] == "hair_long_02"
    avatar = db.query(PlayerAvatar).filter(PlayerAvatar.player_id == body["data"]["id"]).one()
    assert avatar.skin_tone_code == "skin_06"
    assert avatar.hair_color_code == "hair_auburn"
    PlayerSnapshotData.model_validate(body["data"])


def test_registration_rejects_unknown_avatar_identity(client):
    test_client, _db = client
    body = test_client.post(
        "/api/player/register",
        json={
            "username": "invalid-avatar",
            "avatar": {
                "body_preset_code": "giant_body",
            },
        },
    ).json()

    assert body["success"] is False
    assert body["message"] == "Невідомий варіант статури."


def test_avatar_catalog_exposes_small_body_set_and_twenty_faces(client):
    test_client, _db = client
    body = test_client.get("/api/avatar/catalog").json()

    assert body["success"] is True
    catalog = AvatarCatalogData.model_validate(body["data"])
    assert catalog.body_presets == ["body_standard", "body_sturdy"]
    assert len(catalog.face_presets) == 20
    assert catalog.face_presets[0] == "face_01"
    assert catalog.face_presets[-1] == "face_20"
    assert catalog.animation_profile_code == "humanoid_context_v1"


def test_registration_rejects_unknown_tutorial_age_group(client):
    test_client, _db = client
    response = test_client.post(
        "/api/player/register",
        json={"username": "unknown-age", "tutorial_age_group": "unknown"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("username", [" ", "a", "x" * 25])
def test_registration_rejects_invalid_username_length(client, username):
    test_client, _db = client
    body = test_client.post("/api/player/register", json={"username": username}).json()

    assert body["success"] is False
    assert body["message"] == "Ім'я має містити від 2 до 24 символів."


def test_registration_trims_username(client):
    test_client, db = client
    body = test_client.post(
        "/api/player/register",
        json={"username": "  New Citizen  ", "tutorial_age_group": "mature"},
    ).json()

    assert body["success"] is True
    assert body["data"]["username"] == "New Citizen"
    player = db.query(Player).filter(Player.id == body["data"]["id"]).one()
    assert player.username == "New Citizen"
    assert player.tutorial_age_group == "mature"


def test_player_can_find_housing_and_complete_arrival_idempotently(client):
    test_client, _db = client
    register, headers = register_player(test_client, "direct-housing")
    player_id = register["data"]["id"]

    completed = choose_path(test_client, player_id, headers, FIND_HOUSING, "arrival-housing")
    assert completed["success"] is True
    assert completed["data"]["onboarding"]["stage"] == COMPLETED
    assert completed["data"]["onboarding"]["completed"] is True
    assert completed["data"]["hostel"] != "Немає"
    assert completed["data"]["actions"]["can_apply_job"] is True
    PlayerSnapshotData.model_validate(completed["data"])

    repeated = choose_path(test_client, player_id, headers, FIND_HOUSING, "arrival-housing")
    assert repeated == completed


def test_police_report_then_housing_records_the_crime(client):
    test_client, db = client
    register, headers = register_player(test_client, "police-route")
    player_id = register["data"]["id"]

    reported = choose_path(test_client, player_id, headers, REPORT_TO_POLICE, "arrival-police")
    assert reported["success"] is True
    assert reported["data"]["onboarding"]["stage"] == HOUSING_SEARCH
    assert reported["data"]["onboarding"]["available_choices"] == [FIND_HOUSING]
    assert db.query(PoliceRecord).filter(PoliceRecord.player_id == player_id).count() == 1

    completed = choose_path(test_client, player_id, headers, FIND_HOUSING, "arrival-after-police")
    assert completed["success"] is True
    assert completed["data"]["onboarding"]["stage"] == COMPLETED
    assert completed["data"]["hostel"] != "Немає"


def test_due_police_recovery_credits_player_once(client):
    test_client, db = client
    register, headers = register_player(test_client, "police-recovery")
    player_id = register["data"]["id"]
    player = db.query(Player).filter(Player.id == player_id).first()
    onboarding = db.query(PlayerOnboarding).filter(PlayerOnboarding.player_id == player.id).one()
    onboarding.stage = COMPLETED
    onboarding.completed_at = datetime.now(UTC)
    onboarding.police_report_status = POLICE_PENDING
    onboarding.police_recovery_amount = Decimal("75.00")
    onboarding.police_recovery_available_at = datetime.now(UTC) - timedelta(minutes=1)
    starting_balance = Decimal(str(player.balance))
    db.commit()

    due_status = test_client.get(
        f"/api/player/{player_id}",
        headers=headers,
    ).json()
    assert due_status["data"]["onboarding"]["police_recovery_claimable"] is True

    claim_headers = {**headers, "Idempotency-Key": "police-recovery-claim"}
    first = test_client.post(
        "/api/player/onboarding/police-recovery",
        json={"player_id": player_id},
        headers=claim_headers,
    ).json()

    assert first["success"] is True
    assert Decimal(str(first["data"]["balance"])) == starting_balance + Decimal("75.00")
    assert first["data"]["onboarding"]["police_report_status"] == POLICE_RECOVERED
    assert first["data"]["onboarding"]["police_recovery_claimable"] is False
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "police_recovery").count() == 1

    repeated = test_client.post(
        "/api/player/onboarding/police-recovery",
        json={"player_id": player_id},
        headers=claim_headers,
    ).json()
    assert repeated == first


def test_legacy_player_without_onboarding_is_treated_as_completed(client):
    test_client, db = client
    city_uuid = db.query(City).one().id

    player = Player(
        city_id=city_uuid,
        username="legacy-player",
        balance=Decimal("500.00"),
        energy=100,
        mood=100,
        hunger=0,
        education_level="High School",
        auth_token="legacy-token",
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    status = test_client.get(
        f"/api/player/{player.id}",
        headers={"X-Player-Token": "legacy-token"},
    ).json()
    assert status["success"] is True
    assert status["data"]["onboarding"]["completed"] is True
    db.refresh(player)
    assert player.auth_token is None
    assert player.auth_token_hash == hash_player_token("legacy-token")
    bind = db.get_bind()

    fresh_db = sessionmaker(autocommit=False, autoflush=False, bind=bind)()
    try:
        persisted_player = fresh_db.query(Player).filter(Player.id == player.id).one()
        assert persisted_player.auth_token is None
        assert persisted_player.auth_token_hash == hash_player_token("legacy-token")
    finally:
        fresh_db.close()
