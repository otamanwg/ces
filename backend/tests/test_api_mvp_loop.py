import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.models import Player, TransactionModelLog
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
    assert register_body["data"]["balance"] == 500.0

    vacancies_res = test_client.get("/api/jobs/vacancies")
    assert vacancies_res.status_code == 200
    vacancies = vacancies_res.json()["data"]["vacancies"]
    hs_job = next(j for j in vacancies if j["min_education"] == "High School")

    apply_res = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": hs_job["id"]},
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["success"] is True

    work_res = test_client.post(f"/api/jobs/work/{player_id}")
    assert work_res.status_code == 200
    work_body = work_res.json()
    assert work_body["success"] is True
    assert work_body["data"]["energy"] == 70
    assert work_body["data"]["balance"] > 500

    sleep_res = test_client.post(f"/api/hostels/sleep/{player_id}")
    assert sleep_res.status_code == 200
    sleep_body = sleep_res.json()
    assert sleep_body["success"] is True
    assert sleep_body["data"]["energy"] == 100

    tick_res = test_client.post("/api/city/tick-day")
    assert tick_res.status_code == 200
    tick_body = tick_res.json()
    assert tick_body["success"] is True
    assert tick_body["data"]["stats"]["players_updated"] == 1
    assert tick_body["data"]["stats"]["rent_collected"] == 15.0

    exam_info = test_client.get("/api/education/exam/info")
    assert exam_info.status_code == 200
    assert len(exam_info.json()["data"]["questions"]) == 5

    # Earn enough for exam: work/sleep cycles
    player = db.query(Player).filter(Player.id == player_id).first()
    while float(player.balance) < 100:
        test_client.post(f"/api/jobs/work/{player_id}")
        test_client.post(f"/api/hostels/sleep/{player_id}")
        db.refresh(player)

    exam = test_client.get("/api/education/exam/info").json()["data"]
    # All correct answers are index 0 in seed exam file
    answers = {str(q["id"]): 0 for q in exam["questions"]}

    submit_res = test_client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
    )
    assert submit_res.status_code == 200
    submit_body = submit_res.json()
    assert submit_body["success"] is True
    assert submit_body["data"]["passed"] is True

    db.refresh(player)
    assert player.education_level == "College"

    vacancies_after = test_client.get("/api/jobs/vacancies").json()["data"]["vacancies"]
    college_job = next(j for j in vacancies_after if j["min_education"] == "College")
    apply_college = test_client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": college_job["id"]},
    )
    assert apply_college.json()["success"] is True

    assert db.query(TransactionModelLog).count() >= 2
