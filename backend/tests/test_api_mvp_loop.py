import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import IdempotencyRecord, Player, TransactionModelLog
from backend.app.seed import seed_initial_data
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

    register_res = test_client.post("/api/player/register", json={"username": "solo-dev"})
    assert register_res.status_code == 200
    register_body = register_res.json()
    assert register_body["success"] is True
    player_id = register_body["data"]["id"]
    player_token = register_body["data"]["auth_token"]
    auth_headers = {"X-Player-Token": player_token}
    assert register_body["data"]["balance"] == 500.0
    register_effects = register_body["effects"]
    next_action = next(e for e in register_effects if e["key"] == "next_action")
    assert next_action["value"] == "Влаштуйтесь на роботу"

    unauth_player = test_client.get(f"/api/player/{player_id}")
    assert unauth_player.status_code == 200
    assert unauth_player.json()["success"] is False

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
    assert "Сесія гравця недійсна" in invalid_apply_body["message"]

    malformed_player = test_client.post(
        "/api/jobs/apply",
        json={"player_id": "not-a-uuid", "job_id": hs_job["id"]},
        headers=auth_headers,
    )
    assert malformed_player.status_code == 200
    malformed_player_body = malformed_player.json()
    assert malformed_player_body["success"] is False
    assert "Сесія гравця недійсна" in malformed_player_body["message"]

    malformed_job = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": "not-a-uuid"},
        headers=auth_headers,
    )
    assert malformed_job.status_code == 200
    malformed_job_body = malformed_job.json()
    assert malformed_job_body["success"] is False
    assert malformed_job_body["message"] == "Вакансію не знайдено."

    work_headers = {"X-Player-Token": player_token, "Idempotency-Key": "api-loop-work-1"}
    work_res = test_client.post(f"/api/jobs/work/{player_id}", headers=work_headers)
    assert work_res.status_code == 200
    work_body = work_res.json()
    assert work_body["success"] is True
    assert work_body["data"]["energy"] == 70
    assert work_body["data"]["balance"] > 500
    transactions_after_work = db.query(TransactionModelLog).count()

    repeat_work = test_client.post(f"/api/jobs/work/{player_id}", headers=work_headers)
    assert repeat_work.status_code == 200
    assert repeat_work.json() == work_body
    assert db.query(TransactionModelLog).count() == transactions_after_work

    sleep_headers = {"X-Player-Token": player_token, "Idempotency-Key": "api-loop-sleep-1"}
    sleep_res = test_client.post(f"/api/hostels/sleep/{player_id}", headers=sleep_headers)
    assert sleep_res.status_code == 200
    sleep_body = sleep_res.json()
    assert sleep_body["success"] is True
    assert sleep_body["data"]["energy"] == 100
    transactions_after_sleep = db.query(TransactionModelLog).count()

    repeat_sleep = test_client.post(f"/api/hostels/sleep/{player_id}", headers=sleep_headers)
    assert repeat_sleep.status_code == 200
    assert repeat_sleep.json() == sleep_body
    assert db.query(TransactionModelLog).count() == transactions_after_sleep

    balance_after_sleep = sleep_body["data"]["balance"]

    tick_res = test_client.post("/api/city/tick-day")
    assert tick_res.status_code == 200
    tick_body = tick_res.json()
    assert tick_body["success"] is True
    assert tick_body["data"]["stats"]["players_updated"] == 1
    assert tick_body["data"]["stats"]["rent_collected"] == 0.0

    player_after_tick = test_client.get(f"/api/player/{player_id}", headers=auth_headers).json()["data"]
    assert player_after_tick["balance"] == balance_after_sleep

    exam_info = test_client.get("/api/education/exam/info")
    assert exam_info.status_code == 200
    assert len(exam_info.json()["data"]["questions"]) == 5

    # Earn enough for exam: work/sleep cycles
    player = db.query(Player).filter(Player.id == player_id).first()
    while float(player.balance) < 100:
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
