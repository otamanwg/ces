#!/usr/bin/env python3
"""Autonomous smoke test: full MVP loop via HTTP (no Godot required)."""

import os
import sys
import time

import httpx

BASE = os.getenv("CITY_API_BASE", "http://127.0.0.1:8000")
USERNAME = f"smoke_{int(time.time())}"


def main() -> int:
    try:
        with httpx.Client(base_url=BASE, timeout=10.0) as client:
            return run_loop(client)
    except httpx.ConnectError:
        print(f"FAIL: backend not reachable at {BASE}")
        print("Start: python -m uvicorn backend.main:app --reload")
        return 1


def run_loop(client: httpx.Client) -> int:
    city = client.get("/api/city/status").json()
    assert city["success"], city
    print(f"OK city: id={city['data']['id']} inflation={city['data']['inflation_rate']}")

    reg = client.post("/api/player/register", json={"username": USERNAME}).json()
    assert reg["success"], reg
    player_id = reg["data"]["id"]
    auth_headers = {"X-Player-Token": reg["data"]["auth_token"]}
    print(f"OK register: {USERNAME} balance={reg['data']['balance']}")

    vacancies = client.get("/api/jobs/vacancies").json()["data"]["vacancies"]
    hs_job = next(j for j in vacancies if j["min_education"] == "High School")
    apply = client.post(
        "/api/jobs/apply",
        json={"player_id": player_id, "job_id": hs_job["id"]},
        headers=auth_headers,
    ).json()
    assert apply["success"], apply
    print(f"OK apply: job_id={hs_job['id']}")

    for cycle in range(4):
        work = client.post(f"/api/jobs/work/{player_id}", headers=auth_headers).json()
        assert work["success"], work
        sleep = client.post(f"/api/hostels/sleep/{player_id}", headers=auth_headers).json()
        assert sleep["success"], sleep
        bal = sleep["data"]["balance"]
        print(f"OK cycle {cycle + 1}: balance={bal:.2f} energy={sleep['data']['energy']}")

    balance_before_tick = bal
    tick = client.post("/api/city/tick-day").json()
    assert tick["success"], tick
    assert tick["data"]["stats"]["rent_collected"] == 0.0, tick
    print(
        "OK day tick: "
        f"players={tick['data']['stats']['players_updated']} "
        f"decay_only (rent via sleep)"
    )

    player = client.get(f"/api/player/{player_id}", headers=auth_headers).json()["data"]
    assert player["balance"] == balance_before_tick, "tick-day must not charge rent after sleep"

    if player["balance"] < 100:
        print(f"FAIL: balance {player['balance']} < 100 for exam")
        return 1

    exam = client.get("/api/education/exam/info").json()["data"]
    answers = {str(q["id"]): 0 for q in exam["questions"]}
    submit = client.post(
        "/api/education/exam/submit",
        json={"player_id": player_id, "answers": answers},
        headers=auth_headers,
    ).json()
    assert submit["success"], submit
    print(f"OK exam: passed={submit['data'].get('passed')} score={submit['data'].get('score')}")

    if submit["data"].get("passed"):
        vacancies2 = client.get("/api/jobs/vacancies").json()["data"]["vacancies"]
        college = next((j for j in vacancies2 if j["min_education"] == "College"), None)
        if college:
            up = client.post(
                "/api/jobs/apply",
                json={"player_id": player_id, "job_id": college["id"]},
                headers=auth_headers,
            ).json()
            assert up["success"], up
            print(f"OK promoted: job_id={college['id']}")

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
