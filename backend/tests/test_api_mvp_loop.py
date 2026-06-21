import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.core.tokens import hash_player_token
from backend.app.database import get_db
from backend.app.models import IdempotencyRecord, Player, TransactionModelLog
from backend.app.schemas.mvp import (
    BusinessBuyActionData,
    BusinessDividendActionData,
    BusinessMarketData,
    CityStatusData,
    DayTickData,
    ExamInfoData,
    ExamSubmitActionData,
    PlayerSnapshotData,
    SportsClubsData,
    SportsTrainActionData,
    VacanciesData,
    WorkActionData,
)
from backend.app.seed import seed_initial_data
from backend.app.services.messages import (
    INVALID_PLAYER_SESSION_MESSAGE,
    JOB_NOT_FOUND_MESSAGE,
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


def complete_onboarding(test_client, register_body):
    player_id = register_body["data"]["id"]
    response = test_client.post(
        "/api/player/onboarding/choose",
        json={"player_id": player_id, "choice": "find_housing"},
        headers={"X-Player-Token": register_body["data"]["auth_token"]},
    ).json()
    assert response["success"] is True
    assert response["data"]["onboarding"]["completed"] is True
    return response


def test_full_mvp_api_loop(client):
    test_client, db = client

    city_res = test_client.get("/api/city/status")
    assert city_res.status_code == 200
    city_body = city_res.json()
    assert city_body["success"] is True
    assert city_body["data"]["name"] == "Київ-Нейтральний"
    assert city_body["data"]["news"][0]["type"] == "business_market"
    assert city_body["data"]["news"][0]["severity"] == "info"
    assert city_body["data"]["news"][0]["priority"] == 40
    assert [district["code"] for district in city_body["data"]["districts"]] == [
        "bus_station",
        "commercial_core",
        "highrise_residential",
        "industrial_edge",
        "suburb_private_sector",
        "outer_land",
    ]
    assert city_body["data"]["districts"][0]["medical_coverage"] == 45
    assert city_body["data"]["districts"][-1]["zone_type"] == "expansion"
    CityStatusData.model_validate(city_body["data"])

    register_res = test_client.post("/api/player/register", json={"username": "solo-dev"})
    assert register_res.status_code == 200
    register_body = register_res.json()
    assert register_body["success"] is True
    player_id = register_body["data"]["id"]
    player_token = register_body["data"]["auth_token"]
    auth_headers = {"X-Player-Token": player_token}
    registered_player = db.query(Player).filter(Player.id == player_id).one()
    assert registered_player.auth_token is None
    assert registered_player.auth_token_hash == hash_player_token(player_token)
    starting_balance = register_body["data"]["balance"]
    assert 300 <= starting_balance <= 400
    assert register_body["data"]["actions"]["can_take_exam"] is False
    register_effects = register_body["effects"]
    next_action = next(e for e in register_effects if e["key"] == "next_action")
    assert next_action["value"] == "Новий початок"

    completed_arrival = complete_onboarding(test_client, register_body)
    assert completed_arrival["data"]["hostel"] != "Немає"

    unauth_player = test_client.get(f"/api/player/{player_id}")
    assert unauth_player.status_code == 200
    assert unauth_player.json()["success"] is False
    assert unauth_player.json()["message"] == INVALID_PLAYER_SESSION_MESSAGE

    authorized_player = test_client.get(f"/api/player/{player_id}", headers=auth_headers)
    assert authorized_player.status_code == 200
    assert authorized_player.json()["success"] is True
    assert "auth_token" not in authorized_player.json()["data"]

    vacancies_res = test_client.get("/api/jobs/vacancies")
    assert vacancies_res.status_code == 200
    vacancies_data = VacanciesData.model_validate(vacancies_res.json()["data"])
    vacancies = [v.model_dump() for v in vacancies_data.vacancies]
    hs_job = next(j for j in vacancies if j["min_education"] == "High School")

    apply_res = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": hs_job["id"]},
        headers=auth_headers,
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["success"] is True

    invalid_apply = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": hs_job["id"]},
        headers={"X-Player-Token": "invalid-token"},
    )
    assert invalid_apply.status_code == 200
    invalid_apply_body = invalid_apply.json()
    assert invalid_apply_body["success"] is False
    assert invalid_apply_body["message"] == INVALID_PLAYER_SESSION_MESSAGE

    malformed_player = test_client.post(
        "/api/jobs/apply",
        json={"player_id": "not-a-uuid", "job_id": hs_job["id"]},
        headers=auth_headers,
    )
    assert malformed_player.status_code == 200
    malformed_player_body = malformed_player.json()
    assert malformed_player_body["success"] is False
    assert malformed_player_body["message"] == INVALID_PLAYER_SESSION_MESSAGE

    malformed_job = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": "not-a-uuid"},
        headers=auth_headers,
    )
    assert malformed_job.status_code == 200
    malformed_job_body = malformed_job.json()
    assert malformed_job_body["success"] is False
    assert malformed_job_body["message"] == JOB_NOT_FOUND_MESSAGE

    work_headers = {
        "X-Player-Token": player_token,
        "Idempotency-Key": "api-loop-work-1",
    }
    work_res = test_client.post(f"/api/jobs/work/{player_id}", headers=work_headers)
    assert work_res.status_code == 200
    work_body = work_res.json()
    assert work_body["success"] is True
    WorkActionData.model_validate(work_body["data"])
    assert work_body["data"]["energy"] == 70
    assert work_body["data"]["hunger"] == 20
    assert work_body["data"]["balance"] > starting_balance
    transactions_after_work = db.query(TransactionModelLog).count()

    repeat_work = test_client.post(f"/api/jobs/work/{player_id}", headers=work_headers)
    assert repeat_work.status_code == 200
    assert repeat_work.json() == work_body
    assert db.query(TransactionModelLog).count() == transactions_after_work

    malformed_work = test_client.post("/api/jobs/work/not-a-uuid", headers=auth_headers)
    assert malformed_work.status_code == 200
    malformed_work_body = malformed_work.json()
    assert malformed_work_body["success"] is False
    assert malformed_work_body["message"] == INVALID_PLAYER_SESSION_MESSAGE

    sleep_headers = {
        "X-Player-Token": player_token,
        "Idempotency-Key": "api-loop-sleep-1",
    }
    sleep_res = test_client.post(f"/api/hostels/sleep/{player_id}", headers=sleep_headers)
    assert sleep_res.status_code == 200
    sleep_body = sleep_res.json()
    assert sleep_body["success"] is True
    PlayerSnapshotData.model_validate(sleep_body["data"])
    assert sleep_body["data"]["energy"] == 100
    assert sleep_body["data"]["hunger"] == 30
    transactions_after_sleep = db.query(TransactionModelLog).count()

    repeat_sleep = test_client.post(f"/api/hostels/sleep/{player_id}", headers=sleep_headers)
    assert repeat_sleep.status_code == 200
    assert repeat_sleep.json() == sleep_body
    assert db.query(TransactionModelLog).count() == transactions_after_sleep

    malformed_sleep = test_client.post("/api/hostels/sleep/not-a-uuid", headers=auth_headers)
    assert malformed_sleep.status_code == 200
    malformed_sleep_body = malformed_sleep.json()
    assert malformed_sleep_body["success"] is False
    assert malformed_sleep_body["message"] == INVALID_PLAYER_SESSION_MESSAGE

    balance_after_sleep = sleep_body["data"]["balance"]

    tick_res = test_client.post("/api/city/tick-day")
    assert tick_res.status_code == 200
    tick_body = tick_res.json()
    assert tick_body["success"] is True
    assert tick_body["data"]["stats"]["players_updated"] == 1
    assert tick_body["data"]["stats"]["rent_collected"] == 0.0
    assert tick_body["data"]["news"][0]["type"] == "day_tick"
    assert tick_body["data"]["news"][0]["severity"] == "info"
    assert tick_body["data"]["news"][0]["priority"] == 20
    DayTickData.model_validate(tick_body["data"])

    player_after_tick = test_client.get(f"/api/player/{player_id}", headers=auth_headers).json()["data"]
    assert player_after_tick["balance"] == balance_after_sleep

    exam_info = test_client.get("/api/education/exam/info")
    assert exam_info.status_code == 200
    exam_info_data = ExamInfoData.model_validate(exam_info.json()["data"])
    assert len(exam_info_data.questions) == 5

    # Earn enough for exam: target MVP loop is one work/sleep cycle from the starter state.
    player = db.query(Player).filter(Player.id == player_id).first()
    while float(player.balance) < exam_info_data.cost_to_take:
        test_client.post(f"/api/jobs/work/{player_id}", headers=auth_headers)
        test_client.post(f"/api/hostels/sleep/{player_id}", headers=auth_headers)
        db.refresh(player)

    exam = ExamInfoData.model_validate(test_client.get("/api/education/exam/info").json()["data"])
    # All correct answers are index 0 in seed exam file
    answers = {str(q.id): 0 for q in exam.questions}

    exam_headers = {
        "X-Player-Token": player_token,
        "Idempotency-Key": "api-loop-exam-1",
    }
    submit_res = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
        headers=exam_headers,
    )
    assert submit_res.status_code == 200
    submit_body = submit_res.json()
    assert submit_body["success"] is True
    ExamSubmitActionData.model_validate(submit_body["data"])
    assert submit_body["data"]["passed"] is True
    balance_after_exam = submit_body["data"]["balance"]

    repeat_submit = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
        headers=exam_headers,
    )
    assert repeat_submit.status_code == 200
    assert repeat_submit.json() == submit_body
    assert repeat_submit.json()["data"]["balance"] == balance_after_exam

    malformed_exam = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": "not-a-uuid", "answers": answers},
        headers=auth_headers,
    )
    assert malformed_exam.status_code == 200
    malformed_exam_body = malformed_exam.json()
    assert malformed_exam_body["success"] is False
    assert malformed_exam_body["message"] == INVALID_PLAYER_SESSION_MESSAGE

    db.refresh(player)
    assert player.education_level == "College"

    balance_after_pass = player.balance
    second_exam = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
        headers={"X-Player-Token": player_token, "Idempotency-Key": "api-loop-exam-2"},
    )
    assert second_exam.status_code == 200
    second_exam_body = second_exam.json()
    assert second_exam_body["success"] is False
    assert "High School до College" in second_exam_body["message"]
    db.refresh(player)
    assert player.balance == balance_after_pass

    vacancies_after = [
        v.model_dump()
        for v in VacanciesData.model_validate(test_client.get("/api/jobs/vacancies").json()["data"]).vacancies
    ]
    college_job = next(j for j in vacancies_after if j["min_education"] == "College")
    apply_college = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": college_job["id"]},
        headers=auth_headers,
    )
    assert apply_college.json()["success"] is True

    assert db.query(TransactionModelLog).count() >= 2
    assert db.query(IdempotencyRecord).count() == 3


def test_business_market_and_buy_endpoint_are_idempotent(client):
    test_client, db = client

    register = test_client.post("/api/player/register", json={"username": "api-owner"}).json()
    complete_onboarding(test_client, register)
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}

    market_res = test_client.get("/api/businesses/market")
    assert market_res.status_code == 200
    market_body = market_res.json()
    assert market_body["success"] is True
    market_data = BusinessMarketData.model_validate(market_body["data"])
    assert len(market_data.businesses) == 1
    business = market_data.businesses[0].model_dump()
    assert business["type"] == "shop"
    assert business["purchase_price"] == 1200.0

    player = db.query(Player).filter(Player.id == player_id).first()
    player.balance = Decimal("1500.00")
    db.commit()

    buy_payload = {"player_id": player_id, "business_id": business["id"]}
    buy_headers = {**headers, "Idempotency-Key": "api-business-buy-1"}
    buy_res = test_client.post("/api/businesses/buy", json=buy_payload, headers=buy_headers)
    assert buy_res.status_code == 200
    buy_body = buy_res.json()
    assert buy_body["success"] is True
    BusinessBuyActionData.model_validate(buy_body["data"])
    assert buy_body["data"]["balance"] == 300.0
    assert buy_body["data"]["owned_businesses"][0]["name"] == business["name"]
    transactions_after_buy = db.query(TransactionModelLog).count()

    repeat_buy = test_client.post("/api/businesses/buy", json=buy_payload, headers=buy_headers)
    assert repeat_buy.status_code == 200
    assert repeat_buy.json() == buy_body
    assert db.query(TransactionModelLog).count() == transactions_after_buy

    malformed_buy = test_client.post(
        "/api/businesses/buy",
        json={"player_id": player_id, "business_id": "not-a-uuid"},
        headers=headers,
    )
    assert malformed_buy.status_code == 200
    assert malformed_buy.json()["success"] is False
    assert malformed_buy.json()["message"] == "Бізнес не знайдено"


def test_business_dividend_endpoint_is_idempotent(client):
    test_client, db = client

    register = test_client.post("/api/player/register", json={"username": "api-dividend-owner"}).json()
    complete_onboarding(test_client, register)
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}
    player = db.query(Player).filter(Player.id == player_id).first()
    player.balance = Decimal("1500.00")
    db.commit()

    business = test_client.get("/api/businesses/market").json()["data"]["businesses"][0]
    buy_payload = {"player_id": player_id, "business_id": business["id"]}
    buy_res = test_client.post(
        "/api/businesses/buy",
        json=buy_payload,
        headers={**headers, "Idempotency-Key": "api-dividend-buy"},
    ).json()
    assert buy_res["success"] is True

    dividend_headers = {**headers, "Idempotency-Key": "api-dividend-1"}
    dividend_res = test_client.post("/api/businesses/dividend", json=buy_payload, headers=dividend_headers)
    assert dividend_res.status_code == 200
    dividend_body = dividend_res.json()
    assert dividend_body["success"] is True
    BusinessDividendActionData.model_validate(dividend_body["data"])
    assert dividend_body["data"]["balance"] == 400.0
    assert dividend_body["data"]["dividend"] == 100.0
    assert dividend_body["data"]["business"]["cash_balance"] == 900.0
    transactions_after_dividend = db.query(TransactionModelLog).count()

    repeat_dividend = test_client.post("/api/businesses/dividend", json=buy_payload, headers=dividend_headers)
    assert repeat_dividend.status_code == 200
    assert repeat_dividend.json() == dividend_body
    assert db.query(TransactionModelLog).count() == transactions_after_dividend

    malformed_dividend = test_client.post(
        "/api/businesses/dividend",
        json={"player_id": player_id, "business_id": "not-a-uuid"},
        headers=headers,
    )
    assert malformed_dividend.status_code == 200
    assert malformed_dividend.json()["success"] is False
    assert malformed_dividend.json()["message"] == "Бізнес не знайдено"


def test_sports_join_and_train_are_idempotent(client):
    test_client, db = client

    register = test_client.post("/api/player/register", json={"username": "api-athlete"}).json()
    complete_onboarding(test_client, register)
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}
    starting_balance = register["data"]["balance"]

    clubs_res = test_client.get("/api/sports/clubs")
    assert clubs_res.status_code == 200
    clubs_body = clubs_res.json()
    assert clubs_body["success"] is True
    clubs_data = SportsClubsData.model_validate(clubs_body["data"])
    club = clubs_data.clubs[0].model_dump()
    assert club["salary_per_match"] == 120.0

    join_payload = {"player_id": player_id, "club_id": club["id"]}
    join_headers = {**headers, "Idempotency-Key": "api-sports-join-1"}
    join_res = test_client.post("/api/sports/join", json=join_payload, headers=join_headers)
    assert join_res.status_code == 200
    join_body = join_res.json()
    assert join_body["success"] is True
    PlayerSnapshotData.model_validate(join_body["data"])
    assert join_body["data"]["sports_contract"]["strength"] == 10

    repeat_join = test_client.post("/api/sports/join", json=join_payload, headers=join_headers)
    assert repeat_join.status_code == 200
    assert repeat_join.json() == join_body

    train_payload = {"player_id": player_id, "stat_type": "strength"}
    train_headers = {**headers, "Idempotency-Key": "api-sports-train-1"}
    train_res = test_client.post("/api/sports/train", json=train_payload, headers=train_headers)
    assert train_res.status_code == 200
    train_body = train_res.json()
    assert train_body["success"] is True
    SportsTrainActionData.model_validate(train_body["data"])
    assert train_body["data"]["balance"] == starting_balance - 40
    assert train_body["data"]["energy"] == 60
    assert train_body["data"]["sports_contract"]["strength"] >= 12
    transactions_after_train = db.query(TransactionModelLog).count()

    repeat_train = test_client.post("/api/sports/train", json=train_payload, headers=train_headers)
    assert repeat_train.status_code == 200
    assert repeat_train.json() == train_body
    assert db.query(TransactionModelLog).count() == transactions_after_train

    malformed_train = test_client.post(
        "/api/sports/train",
        json={"player_id": player_id, "stat_type": "unknown"},
        headers=headers,
    )
    assert malformed_train.status_code == 200
    assert malformed_train.json()["success"] is False
    assert malformed_train.json()["message"] == "Невідомий тип тренування"


def test_eat_endpoint_is_idempotent_and_logs_food(client):
    test_client, db = client

    register = test_client.post("/api/player/register", json={"username": "api-hungry"}).json()
    complete_onboarding(test_client, register)
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}
    starting_balance = register["data"]["balance"]

    player = db.query(Player).filter(Player.id == player_id).first()
    player.hunger = 80
    db.commit()

    eat_headers = {**headers, "Idempotency-Key": "api-eat-1"}
    eat_res = test_client.post(f"/api/needs/eat/{player_id}", headers=eat_headers)
    assert eat_res.status_code == 200
    eat_body = eat_res.json()
    assert eat_body["success"] is True
    PlayerSnapshotData.model_validate(eat_body["data"])
    assert eat_body["data"]["balance"] == starting_balance - 25
    assert eat_body["data"]["hunger"] == 45
    transactions_after_eat = db.query(TransactionModelLog).count()

    repeat_eat = test_client.post(f"/api/needs/eat/{player_id}", headers=eat_headers)
    assert repeat_eat.status_code == 200
    assert repeat_eat.json() == eat_body
    assert db.query(TransactionModelLog).count() == transactions_after_eat

    malformed_eat = test_client.post("/api/needs/eat/not-a-uuid", headers=headers)
    assert malformed_eat.status_code == 200
    assert malformed_eat.json()["success"] is False
    assert malformed_eat.json()["message"] == INVALID_PLAYER_SESSION_MESSAGE


def test_idempotency_key_is_scoped_by_action_and_player(client):
    test_client, db = client

    first_register = test_client.post("/api/player/register", json={"username": "idempotent-one"}).json()
    second_register = test_client.post("/api/player/register", json={"username": "idempotent-two"}).json()
    complete_onboarding(test_client, first_register)
    complete_onboarding(test_client, second_register)
    first_player_id = first_register["data"]["id"]
    second_player_id = second_register["data"]["id"]
    first_headers = {"X-Player-Token": first_register["data"]["auth_token"]}
    second_headers = {"X-Player-Token": second_register["data"]["auth_token"]}

    vacancies = test_client.get("/api/jobs/vacancies").json()["data"]["vacancies"]
    starter_job = next(j for j in vacancies if j["min_education"] == "High School")
    apply_res = test_client.post(
        "/api/jobs/apply",
        json={"player_id": first_player_id, "job_id": starter_job["id"]},
        headers=first_headers,
    )
    assert apply_res.json()["success"] is True

    shared_key = "shared-client-key"
    first_sleep = test_client.post(
        f"/api/hostels/sleep/{first_player_id}",
        headers={**first_headers, "Idempotency-Key": shared_key},
    ).json()
    assert first_sleep["success"] is True
    assert first_sleep["data"]["id"] == first_player_id

    second_sleep = test_client.post(
        f"/api/hostels/sleep/{second_player_id}",
        headers={**second_headers, "Idempotency-Key": shared_key},
    ).json()
    assert second_sleep["success"] is True
    assert second_sleep["data"]["id"] == second_player_id

    first_work = test_client.post(
        f"/api/jobs/work/{first_player_id}",
        headers={**first_headers, "Idempotency-Key": shared_key},
    ).json()
    assert first_work["success"] is True
    assert first_work["data"]["id"] == first_player_id
    assert first_work["message"] != first_sleep["message"]

    assert db.query(IdempotencyRecord).count() == 3
