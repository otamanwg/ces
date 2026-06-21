import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import (
    Building,
    BuildingApplication,
    Business,
    BusinessBlueprint,
    City,
    LandParcel,
    Player,
    TransactionModelLog,
)
from backend.app.schemas.mvp import (
    BuildingActivationActionData,
    BuildingApplicationData,
    BuildingOpenActionData,
    BuildingPortfolioData,
    BuildingRepairActionData,
    BusinessBlueprintsData,
    LandParcelsData,
    LandPurchaseActionData,
)
from backend.app.seed import seed_initial_data
from backend.app.services.buildings import (
    ACTIVE,
    BUILDING_REPAIR_PURPOSE,
    MAINTENANCE_DUE,
)
from backend.app.services.land import OWNED
from backend.app.services.messages import INVALID_PLAYER_SESSION_MESSAGE
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
    player_id = body["data"]["id"]
    token = body["data"]["auth_token"]
    onboarding = test_client.post(
        "/api/player/onboarding/choose",
        json={"player_id": player_id, "choice": "find_housing"},
        headers={"X-Player-Token": token},
    ).json()
    assert onboarding["success"] is True
    return player_id, token


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


def test_business_blueprints_endpoint_returns_starter_catalog(client):
    test_client, _db = client

    res = test_client.get("/api/business/blueprints")

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BusinessBlueprintsData.model_validate(body["data"])
    blueprints = {blueprint.code: blueprint for blueprint in data.blueprints}
    assert len(blueprints) == 11  # 7 starter + 3 utility (G3) + 1 bank (G5)
    assert blueprints["station_kiosk"].project_type == "commercial"
    assert blueprints["station_kiosk"].business_type == "shop"
    assert blueprints["station_kiosk"].metric_effects["expected_jobs"] == 2
    assert blueprints["small_factory"].risk_level == 5
    assert blueprints["private_hostel"].business_type == "private_hostel"


def test_player_can_create_first_physical_building_from_public_catalog(client):
    test_client, db = client
    player_id, token = register_player(test_client, "first-physical-builder")

    parcels_res = test_client.get("/api/land/parcels")
    assert parcels_res.status_code == 200
    parcels = LandParcelsData.model_validate(parcels_res.json()["data"]).parcels
    parcel = next(parcel for parcel in parcels if parcel.code == "bus_station_kiosk_lot")

    blueprints_res = test_client.get("/api/business/blueprints")
    assert blueprints_res.status_code == 200
    blueprints = BusinessBlueprintsData.model_validate(blueprints_res.json()["data"]).blueprints
    blueprint = next(blueprint for blueprint in blueprints if blueprint.code == "station_kiosk")

    headers = {"X-Player-Token": token, "Idempotency-Key": "first-building-land"}
    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": parcel.id},
        headers=headers,
    )
    assert buy_res.status_code == 200
    buy_body = buy_res.json()
    assert buy_body["success"] is True
    buy_data = LandPurchaseActionData.model_validate(buy_body["data"])
    assert buy_data.land_parcel.id == parcel.id
    assert buy_data.land_parcel.status == "owned"

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": parcel.id,
            "business_blueprint_id": blueprint.id,
        },
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": "first-building-application",
        },
    )
    assert application_res.status_code == 200
    application_body = application_res.json()
    assert application_body["success"] is True
    application = BuildingApplicationData.model_validate(application_body["data"])
    assert application.status == "approved"
    assert application.business_blueprint_id == blueprint.id
    assert application.proposed_name == blueprint.name
    assert application.project_type == blueprint.project_type

    activation_res = test_client.post(
        f"/api/building/applications/{application.id}/activate",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": "first-building-activation",
        },
    )
    assert activation_res.status_code == 200
    activation_body = activation_res.json()
    assert activation_body["success"] is True
    activation = BuildingActivationActionData.model_validate(activation_body["data"])
    assert activation.building.land_parcel_id == parcel.id
    assert activation.building.business_blueprint_id == blueprint.id
    assert activation.building.status == "built"
    assert activation.building.operating_status == "inactive"

    portfolio_res = test_client.get(
        f"/api/player/{player_id}/buildings",
        headers={"X-Player-Token": token},
    )
    assert portfolio_res.status_code == 200
    portfolio_body = portfolio_res.json()
    assert portfolio_body["success"] is True
    portfolio = BuildingPortfolioData.model_validate(portfolio_body["data"])
    assert len(portfolio.buildings) == 1
    item = portfolio.buildings[0]
    assert item.id == activation.building.id
    assert item.land_parcel_id == parcel.id
    assert item.blueprint_code == blueprint.code
    assert item.blueprint_name == blueprint.name
    assert item.opening_fee == blueprint.opening_fee
    assert item.upkeep_daily == blueprint.upkeep_daily
    assert item.available_actions == ["open"]

    db_parcel = db.query(LandParcel).filter(LandParcel.id == parcel.id).one()
    assert db_parcel.status == "built"


def test_land_purchase_transfers_money_to_treasury_assigns_owner_and_is_idempotent(
    client,
):
    test_client, db = client
    player_id, token = register_player(test_client, "land-buyer")
    player = db.query(Player).filter(Player.id == player_id).one()
    city = db.query(City).filter(City.id == player.city_id).one()
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    player.balance = Decimal("500.00")
    db.commit()
    starting_treasury = Decimal(str(city.treasury_balance))

    payload = {"player_id": player_id, "land_parcel_id": str(parcel.id)}
    headers = {"X-Player-Token": token, "Idempotency-Key": "land-buy-1"}
    res = test_client.post("/api/land/buy", json=payload, headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = LandPurchaseActionData.model_validate(body["data"])
    assert data.balance == 300.0
    assert data.land_parcel.id == str(parcel.id)
    assert data.land_parcel.status == "owned"
    assert data.land_parcel.owner_player_id == player_id

    db.refresh(player)
    db.refresh(city)
    db.refresh(parcel)
    assert Decimal(str(player.balance)) == Decimal("300.00")
    assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("200.00")
    assert parcel.owner_player_id == player.id
    assert parcel.status == "owned"

    land_purchase_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "land_purchase").one()
    assert land_purchase_log.sender_id == player.id
    assert land_purchase_log.sender_type == "player"
    assert land_purchase_log.receiver_id == city.id
    assert land_purchase_log.receiver_type == "treasury"
    assert land_purchase_log.amount == Decimal("200.00")

    repeat = test_client.post("/api/land/buy", json=payload, headers=headers)
    assert repeat.status_code == 200
    assert repeat.json() == body
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "land_purchase").count() == 1


def test_land_purchase_requires_enough_money(client):
    test_client, db = client
    player_id, token = register_player(test_client, "poor-land-buyer")
    player = db.query(Player).filter(Player.id == player_id).one()
    parcel = db.query(LandParcel).filter(LandParcel.code == "outer_expansion_lot").one()
    starting_balance = Decimal(str(player.balance))

    res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert "Недостатньо коштів для купівлі землі" in body["message"]
    db.refresh(player)
    db.refresh(parcel)
    assert Decimal(str(player.balance)) == starting_balance
    assert parcel.owner_player_id is None
    assert parcel.status == "city_owned"
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "land_purchase").count() == 0


def test_land_purchase_rejects_owned_parcel(client):
    test_client, db = client
    first_player_id, first_token = register_player(test_client, "first-land-owner")
    second_player_id, second_token = register_player(test_client, "second-land-owner")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()

    first_res = test_client.post(
        "/api/land/buy",
        json={"player_id": first_player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": first_token},
    )
    assert first_res.json()["success"] is True

    second_res = test_client.post(
        "/api/land/buy",
        json={"player_id": second_player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": second_token},
    )

    assert second_res.status_code == 200
    body = second_res.json()
    assert body["success"] is False
    assert body["message"] == "Ця ділянка вже має власника."
    db.refresh(parcel)
    assert str(parcel.owner_player_id) == first_player_id


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


def test_building_application_blueprint_is_metric_source_of_truth(client):
    test_client, db = client
    player_id, token = register_player(test_client, "blueprint-builder")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "station_kiosk").one()

    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token, "Idempotency-Key": "blueprint-land-buy"},
    ).json()
    assert buy_res["success"] is True

    res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "business_blueprint_id": str(blueprint.id),
            "proposed_name": "",
            "project_type": "industrial",
            "expected_jobs": 99,
            "traffic_load": 99,
            "service_load": 99,
            "medical_load": 99,
            "public_benefit": 0,
        },
        headers={"X-Player-Token": token, "Idempotency-Key": "blueprint-application"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingApplicationData.model_validate(body["data"])
    assert data.business_blueprint_id == str(blueprint.id)
    assert data.proposed_name == "Вокзальний кіоск"
    assert data.project_type == "commercial"
    assert data.expected_jobs == 2
    assert data.traffic_load == 3
    assert data.service_load == 2
    assert data.medical_load == 1
    assert data.public_benefit == 5
    assert data.status == "approved"


def test_building_application_blueprint_validates_land_requirements(client):
    test_client, db = client
    player_id, token = register_player(test_client, "wrong-blueprint-builder")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "coffee_shop").one()

    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token},
    ).json()
    assert buy_res["success"] is True

    res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "business_blueprint_id": str(blueprint.id),
        },
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert "потрібна ділянка" in body["message"]
    assert db.query(BuildingApplication).count() == 0


def test_approved_building_application_activation_creates_building_and_is_idempotent(
    client,
):
    test_client, db = client
    player_id, token = register_player(test_client, "approved-builder")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()

    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token, "Idempotency-Key": "activation-land-buy"},
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "proposed_name": "Вокзальний кіоск",
            "project_type": "commercial",
            "expected_jobs": 2,
            "traffic_load": 3,
            "service_load": 2,
            "medical_load": 1,
        },
        headers={"X-Player-Token": token, "Idempotency-Key": "activation-application"},
    ).json()
    assert application_res["success"] is True
    application_id = application_res["data"]["id"]
    assert application_res["data"]["status"] == "approved"

    activate_headers = {"X-Player-Token": token, "Idempotency-Key": "activation-1"}
    activate_res = test_client.post(
        f"/api/building/applications/{application_id}/activate",
        json={"player_id": player_id},
        headers=activate_headers,
    )

    assert activate_res.status_code == 200
    body = activate_res.json()
    assert body["success"] is True
    data = BuildingActivationActionData.model_validate(body["data"])
    assert data.building.name == "Вокзальний кіоск"
    assert data.building.status == "built"
    assert data.building.operating_status == "inactive"
    assert data.building.owner_player_id == player_id

    db.refresh(parcel)
    application = db.query(BuildingApplication).filter(BuildingApplication.id == application_id).one()
    assert parcel.status == "built"
    assert application.status == "activated"
    assert db.query(Building).count() == 1

    repeat = test_client.post(
        f"/api/building/applications/{application_id}/activate",
        json={"player_id": player_id},
        headers=activate_headers,
    )
    assert repeat.status_code == 200
    assert repeat.json() == body
    assert db.query(Building).count() == 1


def create_openable_commercial_building(test_client, db, player_id: str, token: str):
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token, "Idempotency-Key": f"open-land-{player_id}"},
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "proposed_name": "Вокзальна кав'ярня",
            "project_type": "commercial",
            "expected_jobs": 3,
            "traffic_load": 3,
            "service_load": 2,
            "medical_load": 1,
        },
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"open-application-{player_id}",
        },
    ).json()
    assert application_res["success"] is True

    activate_res = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"open-activate-{player_id}",
        },
    ).json()
    assert activate_res["success"] is True
    return activate_res["data"]["building"]["id"]


def create_inactive_blueprint_building(test_client, db, player_id: str, token: str):
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "station_kiosk").one()

    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"portfolio-land-{player_id}",
        },
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "business_blueprint_id": str(blueprint.id),
            "proposed_name": "Портфельний кіоск",
        },
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"portfolio-application-{player_id}",
        },
    ).json()
    assert application_res["success"] is True

    activate_res = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"portfolio-activate-{player_id}",
        },
    ).json()
    assert activate_res["success"] is True
    return activate_res["data"]["building"]["id"]


def create_opened_blueprint_building(test_client, db, player_id: str, token: str):
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "station_kiosk").one()

    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"repair-land-{player_id}",
        },
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "business_blueprint_id": str(blueprint.id),
            "proposed_name": "Ремонтний кіоск",
        },
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"repair-application-{player_id}",
        },
    ).json()
    assert application_res["success"] is True

    activate_res = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"repair-activate-{player_id}",
        },
    ).json()
    assert activate_res["success"] is True

    open_res = test_client.post(
        f"/api/buildings/{activate_res['data']['building']['id']}/open",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": f"repair-open-{player_id}",
        },
    ).json()
    assert open_res["success"] is True
    return activate_res["data"]["building"]["id"]


def test_open_building_charges_fee_links_business_and_is_idempotent(client):
    test_client, db = client
    player_id, token = register_player(test_client, "building-operator")
    player = db.query(Player).filter(Player.id == player_id).one()
    city = db.query(City).filter(City.id == player.city_id).one()
    player.balance = Decimal("500.00")
    db.commit()
    building_id = create_openable_commercial_building(test_client, db, player_id, token)
    starting_treasury = Decimal(str(city.treasury_balance))

    headers = {"X-Player-Token": token, "Idempotency-Key": "building-open-1"}
    res = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": player_id},
        headers=headers,
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingOpenActionData.model_validate(body["data"])
    assert data.balance == 200.0
    assert data.opening_fee == 100.0
    assert data.building.id == building_id
    assert data.building.operating_status == "active"
    assert data.building.business_id is not None
    assert data.owned_businesses[0].name == "Вокзальна кав'ярня"

    db.refresh(player)
    db.refresh(city)
    building = db.query(Building).filter(Building.id == building_id).one()
    business = db.query(Business).filter(Business.id == building.business_id).one()
    assert Decimal(str(player.balance)) == Decimal("200.00")
    assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("100.00")
    assert building.operating_status == "active"
    assert business.owner_player_id == player.id
    assert business.type == "shop"
    assert business.cash_balance == Decimal("0.00")

    opening_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "building_opening_fee").one()
    assert opening_log.sender_id == player.id
    assert opening_log.sender_type == "player"
    assert opening_log.receiver_id == city.id
    assert opening_log.receiver_type == "treasury"
    assert opening_log.amount == Decimal("100.00")

    repeat = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": player_id},
        headers=headers,
    )
    assert repeat.status_code == 200
    assert repeat.json() == body
    assert db.query(Business).filter(Business.name == "Вокзальна кав'ярня").count() == 1
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "building_opening_fee").count() == 1


def test_building_portfolio_returns_empty_list_for_new_player(client):
    test_client, _db = client
    player_id, token = register_player(test_client, "empty-building-owner")

    res = test_client.get(
        f"/api/player/{player_id}/buildings",
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingPortfolioData.model_validate(body["data"])
    assert data.buildings == []


def test_building_portfolio_requires_player_session(client):
    test_client, _db = client
    owner_id, _owner_token = register_player(test_client, "portfolio-owner")
    _intruder_id, intruder_token = register_player(test_client, "portfolio-intruder")

    res = test_client.get(
        f"/api/player/{owner_id}/buildings",
        headers={"X-Player-Token": intruder_token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["message"] == INVALID_PLAYER_SESSION_MESSAGE


def test_building_portfolio_exposes_inactive_building_open_action(client):
    test_client, db = client
    player_id, token = register_player(test_client, "inactive-portfolio-owner")
    building_id = create_inactive_blueprint_building(test_client, db, player_id, token)

    res = test_client.get(
        f"/api/player/{player_id}/buildings",
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingPortfolioData.model_validate(body["data"])
    assert len(data.buildings) == 1
    item = data.buildings[0]
    assert item.id == building_id
    assert item.district_code == "bus_station"
    assert item.land_parcel_code == "bus_station_kiosk_lot"
    assert item.blueprint_code == "station_kiosk"
    assert item.business_id is None
    assert item.business_type == "shop"
    assert item.business_cash_balance is None
    assert item.operating_status == "inactive"
    assert item.opening_fee == 100.0
    assert item.repair_fee == 25.0
    assert item.upkeep_daily == 8.0
    assert item.available_actions == ["open"]


def test_building_portfolio_exposes_maintenance_due_repair_action(client):
    test_client, db = client
    player_id, token = register_player(test_client, "repair-portfolio-owner")
    building_id = create_opened_blueprint_building(test_client, db, player_id, token)
    building = db.query(Building).filter(Building.id == building_id).one()
    business = db.query(Business).filter(Business.id == building.business_id).one()
    business.cash_balance = Decimal("42.00")
    building.operating_status = MAINTENANCE_DUE
    db.commit()

    res = test_client.get(
        f"/api/player/{player_id}/buildings",
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingPortfolioData.model_validate(body["data"])
    assert len(data.buildings) == 1
    item = data.buildings[0]
    assert item.id == building_id
    assert item.business_id == str(business.id)
    assert item.business_type == "shop"
    assert item.business_cash_balance == 42.0
    assert item.operating_status == MAINTENANCE_DUE
    assert item.available_actions == ["repair"]
    assert item.repair_fee == 25.0
    assert item.upkeep_daily == 8.0


def test_open_building_uses_blueprint_fee_and_business_type(client):
    test_client, db = client
    player_id, token = register_player(test_client, "hostel-operator")
    player = db.query(Player).filter(Player.id == player_id).one()
    player.balance = Decimal("1000.00")
    parcel = db.query(LandParcel).filter(LandParcel.code == "residential_hostel_lot").one()
    parcel.owner_player_id = player.id
    parcel.status = OWNED
    blueprint = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "private_hostel").one()
    db.commit()

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "business_blueprint_id": str(blueprint.id),
            "proposed_name": "Хостел гравця",
        },
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": "hostel-blueprint-application",
        },
    ).json()
    assert application_res["success"] is True
    assert application_res["data"]["project_type"] == "residential"
    assert application_res["data"]["business_blueprint_id"] == str(blueprint.id)

    activate_res = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": player_id},
        headers={
            "X-Player-Token": token,
            "Idempotency-Key": "hostel-blueprint-activate",
        },
    ).json()
    assert activate_res["success"] is True
    building_id = activate_res["data"]["building"]["id"]
    assert activate_res["data"]["building"]["business_blueprint_id"] == str(blueprint.id)

    open_res = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": player_id},
        headers={"X-Player-Token": token, "Idempotency-Key": "hostel-blueprint-open"},
    )

    assert open_res.status_code == 200
    body = open_res.json()
    assert body["success"] is True
    data = BuildingOpenActionData.model_validate(body["data"])
    assert data.opening_fee == 160.0
    assert data.balance == 840.0
    assert data.building.business_blueprint_id == str(blueprint.id)
    assert data.building.business_id is not None

    building = db.query(Building).filter(Building.id == building_id).one()
    business = db.query(Business).filter(Business.id == building.business_id).one()
    assert business.type == "private_hostel"
    assert business.owner_player_id == player.id


def test_repair_building_charges_fee_reactivates_and_is_idempotent(client):
    test_client, db = client
    player_id, token = register_player(test_client, "repair-operator")
    player = db.query(Player).filter(Player.id == player_id).one()
    city = db.query(City).filter(City.id == player.city_id).one()
    player.balance = Decimal("500.00")
    db.commit()
    building_id = create_opened_blueprint_building(test_client, db, player_id, token)
    building = db.query(Building).filter(Building.id == building_id).one()
    building.operating_status = MAINTENANCE_DUE
    db.commit()
    starting_treasury = Decimal(str(city.treasury_balance))

    headers = {"X-Player-Token": token, "Idempotency-Key": "building-repair-1"}
    res = test_client.post(
        f"/api/buildings/{building_id}/repair",
        json={"player_id": player_id},
        headers=headers,
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = BuildingRepairActionData.model_validate(body["data"])
    assert data.balance == 175.0
    assert data.repair_fee == 25.0
    assert data.building.id == building_id
    assert data.building.operating_status == ACTIVE

    db.refresh(player)
    db.refresh(city)
    db.refresh(building)
    assert Decimal(str(player.balance)) == Decimal("175.00")
    assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal("25.00")
    assert building.operating_status == ACTIVE

    repair_log = db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_REPAIR_PURPOSE).one()
    assert repair_log.sender_id == player.id
    assert repair_log.sender_type == "player"
    assert repair_log.receiver_id == city.id
    assert repair_log.receiver_type == "treasury"
    assert repair_log.amount == Decimal("25.00")

    repeat = test_client.post(
        f"/api/buildings/{building_id}/repair",
        json={"player_id": player_id},
        headers=headers,
    )
    assert repeat.status_code == 200
    assert repeat.json() == body
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_REPAIR_PURPOSE).count() == 1


def test_repair_building_requires_owner(client):
    test_client, db = client
    owner_id, owner_token = register_player(test_client, "repair-owner")
    intruder_id, intruder_token = register_player(test_client, "repair-intruder")
    building_id = create_opened_blueprint_building(test_client, db, owner_id, owner_token)
    building = db.query(Building).filter(Building.id == building_id).one()
    building.operating_status = MAINTENANCE_DUE
    db.commit()

    res = test_client.post(
        f"/api/buildings/{building_id}/repair",
        json={"player_id": intruder_id},
        headers={"X-Player-Token": intruder_token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["message"] == "Ремонтувати можна лише власну будівлю."
    db.refresh(building)
    assert building.operating_status == MAINTENANCE_DUE
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_REPAIR_PURPOSE).count() == 0


def test_repair_building_requires_enough_money(client):
    test_client, db = client
    player_id, token = register_player(test_client, "poor-repair-owner")
    player = db.query(Player).filter(Player.id == player_id).one()
    building_id = create_opened_blueprint_building(test_client, db, player_id, token)
    building = db.query(Building).filter(Building.id == building_id).one()
    building.operating_status = MAINTENANCE_DUE
    player.balance = Decimal("10.00")
    db.commit()

    res = test_client.post(
        f"/api/buildings/{building_id}/repair",
        json={"player_id": player_id},
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert "Недостатньо коштів для ремонту будівлі" in body["message"]
    db.refresh(player)
    db.refresh(building)
    assert Decimal(str(player.balance)) == Decimal("10.00")
    assert building.operating_status == MAINTENANCE_DUE
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_REPAIR_PURPOSE).count() == 0


def test_repair_building_rejects_already_active(client):
    test_client, db = client
    player_id, token = register_player(test_client, "active-repair-owner")
    building_id = create_opened_blueprint_building(test_client, db, player_id, token)

    res = test_client.post(
        f"/api/buildings/{building_id}/repair",
        json={"player_id": player_id},
        headers={"X-Player-Token": token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["message"] == "Будівля вже працює."
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == BUILDING_REPAIR_PURPOSE).count() == 0


def test_open_building_requires_owner(client):
    test_client, db = client
    owner_id, owner_token = register_player(test_client, "building-open-owner")
    intruder_id, intruder_token = register_player(test_client, "building-open-intruder")
    building_id = create_openable_commercial_building(test_client, db, owner_id, owner_token)

    res = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": intruder_id},
        headers={"X-Player-Token": intruder_token},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["message"] == "Відкрити можна лише власну будівлю."
    building = db.query(Building).filter(Building.id == building_id).one()
    assert building.operating_status == "inactive"
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "building_opening_fee").count() == 0


def test_open_building_rejects_already_active_without_idempotency(client):
    test_client, db = client
    player_id, token = register_player(test_client, "already-open-operator")
    building_id = create_openable_commercial_building(test_client, db, player_id, token)

    first = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": player_id},
        headers={"X-Player-Token": token},
    ).json()
    assert first["success"] is True

    second = test_client.post(
        f"/api/buildings/{building_id}/open",
        json={"player_id": player_id},
        headers={"X-Player-Token": token},
    )

    assert second.status_code == 200
    body = second.json()
    assert body["success"] is False
    assert body["message"] == "Будівля вже працює."
    assert db.query(TransactionModelLog).filter(TransactionModelLog.purpose == "building_opening_fee").count() == 1


def test_revision_building_application_cannot_be_activated(client):
    test_client, db = client
    player_id, token = register_player(test_client, "revision-builder")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": player_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": token},
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": player_id,
            "land_parcel_id": str(parcel.id),
            "proposed_name": "Промисловий цех біля вокзалу",
            "project_type": "industrial",
            "expected_jobs": 5,
        },
        headers={"X-Player-Token": token},
    ).json()
    assert application_res["success"] is True
    assert application_res["data"]["status"] == "revision_required"

    activate = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": player_id},
        headers={"X-Player-Token": token},
    )

    assert activate.status_code == 200
    body = activate.json()
    assert body["success"] is False
    assert body["message"] == "Активувати можна лише погоджену AI-мером заявку."
    assert db.query(Building).count() == 0


def test_building_application_activation_requires_applicant(client):
    test_client, db = client
    owner_id, owner_token = register_player(test_client, "activation-owner")
    intruder_id, intruder_token = register_player(test_client, "activation-intruder")
    parcel = db.query(LandParcel).filter(LandParcel.code == "bus_station_kiosk_lot").one()
    buy_res = test_client.post(
        "/api/land/buy",
        json={"player_id": owner_id, "land_parcel_id": str(parcel.id)},
        headers={"X-Player-Token": owner_token},
    ).json()
    assert buy_res["success"] is True

    application_res = test_client.post(
        "/api/building/applications",
        json={
            "player_id": owner_id,
            "land_parcel_id": str(parcel.id),
            "proposed_name": "Магазин власника",
            "project_type": "commercial",
            "expected_jobs": 3,
        },
        headers={"X-Player-Token": owner_token},
    ).json()
    assert application_res["success"] is True

    activate = test_client.post(
        f"/api/building/applications/{application_res['data']['id']}/activate",
        json={"player_id": intruder_id},
        headers={"X-Player-Token": intruder_token},
    )

    assert activate.status_code == 200
    body = activate.json()
    assert body["success"] is False
    assert body["message"] == "Активувати можна лише власну будівельну заявку."
    assert db.query(Building).count() == 0


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
