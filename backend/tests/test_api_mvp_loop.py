import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import IdempotencyRecord, Player, TransactionModelLog
from backend.app.seed import seed_initial_data
from backend.app.services.messages import INVALID_PLAYER_SESSION_MESSAGE, JOB_NOT_FOUND_MESSAGE
from backend.tests.db import make_test_session
from backend.main import app

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


def test_full_mvp_api_loop(client):
    test_client, db = client

    city_res = test_client.get("/api/city/status")
    assert city_res.status_code == 200
    city_body = city_res.json()
    assert city_body["success"] is True
    assert city_body["data"]["name"] == "Київ-Нейтральний"
    assert city_body["data"]["news"][0]["type"] == "business_market"

    register_res = test_client.post("/api/player/register", json={"username": "solo-dev"})
    assert register_res.status_code == 200
    register_body = register_res.json()
    assert register_body["success"] is True
    player_id = register_body["data"]["id"]
    player_token = register_body["data"]["auth_token"]
    auth_headers = {"X-Player-Token": player_token}
    assert register_body["data"]["balance"] == 500.0
    assert register_body["data"]["actions"]["can_take_exam"] is False
    register_effects = register_body["effects"]
    next_action = next(e for e in register_effects if e["key"] == "next_action")
    assert next_action["value"] == "Влаштуйтесь на роботу"

    unauth_player = test_client.get(f"/api/player/{player_id}")
    assert unauth_player.status_code == 200
    assert unauth_player.json()["success"] is False
    assert unauth_player.json()["message"] == INVALID_PLAYER_SESSION_MESSAGE

    vacancies_res = test_client.get("/api/jobs/vacancies")
    assert vacancies_res.status_code == 200
    vacancies = vacancies_res.json()["data"]["vacancies"]
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

    work_headers = {"X-Player-Token": player_token, "Idempotency-Key": "api-loop-work-1"}
    work_res = test_client.post(f"/api/jobs/work/{player_id}", headers=work_headers)
    assert work_res.status_code == 200
    work_body = work_res.json()
    assert work_body["success"] is True
    assert work_body["data"]["energy"] == 70
    assert work_body["data"]["hunger"] == 20
    assert work_body["data"]["balance"] > 500
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

    sleep_headers = {"X-Player-Token": player_token, "Idempotency-Key": "api-loop-sleep-1"}
    sleep_res = test_client.post(f"/api/hostels/sleep/{player_id}", headers=sleep_headers)
    assert sleep_res.status_code == 200
    sleep_body = sleep_res.json()
    assert sleep_body["success"] is True
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

    player_after_tick = test_client.get(f"/api/player/{player_id}", headers=auth_headers).json()["data"]
    assert player_after_tick["balance"] == balance_after_sleep

    exam_info = test_client.get("/api/education/exam/info")
    assert exam_info.status_code == 200
    assert len(exam_info.json()["data"]["questions"]) == 5

    # Earn enough for exam: target MVP loop is one work/sleep cycle from the starter state.
    player = db.query(Player).filter(Player.id == player_id).first()
    while float(player.balance) < exam_info.json()["data"]["cost_to_take"]:
        test_client.post(f"/api/jobs/work/{player_id}", headers=auth_headers)
        test_client.post(f"/api/hostels/sleep/{player_id}", headers=auth_headers)
        db.refresh(player)

    exam = test_client.get("/api/education/exam/info").json()["data"]
    # All correct answers are index 0 in seed exam file
    answers = {str(q["id"]): 0 for q in exam["questions"]}

    exam_headers = {"X-Player-Token": player_token, "Idempotency-Key": "api-loop-exam-1"}
    submit_res = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
        headers=exam_headers,
    )
    assert submit_res.status_code == 200
    submit_body = submit_res.json()
    assert submit_body["success"] is True
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

    vacancies_after = test_client.get("/api/jobs/vacancies").json()["data"]["vacancies"]
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
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}

    market_res = test_client.get("/api/businesses/market")
    assert market_res.status_code == 200
    market_body = market_res.json()
    assert market_body["success"] is True
    assert len(market_body["data"]["businesses"]) == 1
    business = market_body["data"]["businesses"][0]
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


def test_eat_endpoint_is_idempotent_and_logs_food(client):
    test_client, db = client

    register = test_client.post("/api/player/register", json={"username": "api-hungry"}).json()
    player_id = register["data"]["id"]
    headers = {"X-Player-Token": register["data"]["auth_token"]}

    player = db.query(Player).filter(Player.id == player_id).first()
    player.hunger = 80
    db.commit()

    eat_headers = {**headers, "Idempotency-Key": "api-eat-1"}
    eat_res = test_client.post(f"/api/needs/eat/{player_id}", headers=eat_headers)
    assert eat_res.status_code == 200
    eat_body = eat_res.json()
    assert eat_body["success"] is True
    assert eat_body["data"]["balance"] == 475.0
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
