"""
Phase G4 — тести вакансій та найму.

Покриває:
- Фіксована ЗП за типом бізнесу.
- post_player_vacancy: власник виставляє вакансію з bonus_pct.
- apply_for_job: гравець подає заявку (перевірка освіти, зайнятості).
- fire_player: власник звільняє працівника.
- owner_works_shift: власник працює сам (енергія, без ЗП).
- Біржа студентських робіт (shift_type="student").
- API endpoints.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import Business, City, Job, Player
from backend.app.services.vacancy_service import (
    DEFAULT_ENERGY_COST,
    EVENING_SHIFT_ENERGY_COST,
    FIXED_SALARY_BY_BUSINESS_TYPE,
    apply_for_job,
    fire_player,
    get_fixed_salary,
    job_to_dict,
    list_open_vacancies,
    list_student_vacancies,
    owner_works_shift,
    post_player_vacancy,
)
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_city(db) -> City:
    city = City(
        name="VacancyTestCity",
        treasury_balance=Decimal("100000.00"),
        inflation_rate=Decimal("2.5"),
        game_day=0,
    )
    db.add(city)
    db.flush()
    return city


def _make_business(db, city: City, owner: Player | None = None, btype: str = "shop") -> Business:
    business = Business(
        city_id=city.id,
        name=f"TestBiz_{btype}",
        type=btype,
        legal_form="tov",
        cash_balance=Decimal("10000.00"),
        status="active",
        owner_player_id=owner.id if owner else None,
    )
    db.add(business)
    db.flush()
    return business


def _make_player(db, city: City, username: str = "testplayer", energy: int = 100) -> Player:
    player = Player(
        city_id=city.id,
        username=f"{username}_{__name__}",
        balance=Decimal("500.00"),
        energy=energy,
        mood=80,
        hunger=0,
        education_level="High School",
    )
    db.add(player)
    db.flush()
    return player


# --- Фіксована ЗП ---


class TestFixedSalary:
    def test_shop_salary(self):
        assert get_fixed_salary("shop") == FIXED_SALARY_BY_BUSINESS_TYPE["shop"]

    def test_factory_salary_higher_than_shop(self):
        assert get_fixed_salary("factory") > get_fixed_salary("shop")

    def test_unknown_type_uses_default(self):
        assert get_fixed_salary("unknown") == FIXED_SALARY_BY_BUSINESS_TYPE["shop"]


# --- Post vacancy ---


class TestPostVacancy:
    def test_owner_posts_vacancy(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            result = post_player_vacancy(db, business, bonus_pct=Decimal("15.00"))
            db.flush()
            assert result["success"] is True
            assert result["job"]["salary_per_hour"] == float(FIXED_SALARY_BY_BUSINESS_TYPE["shop"])
            assert result["job"]["bonus_pct"] == 15.0
            assert result["job"]["shift_type"] == "day"
        finally:
            db.close()

    def test_bonus_pct_capped(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            result = post_player_vacancy(db, business, bonus_pct=Decimal("100.00"))
            assert result["success"] is False
        finally:
            db.close()

    def test_student_shift_uses_lower_energy(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            result = post_player_vacancy(db, business, shift_type="student")
            db.flush()
            assert result["success"] is True
            job = db.query(Job).filter(Job.id == __import__("uuid").UUID(result["job"]["id"])).first()
            assert job.energy_cost_per_shift == EVENING_SHIFT_ENERGY_COST
        finally:
            db.close()


# --- Apply for job ---


class TestApplyForJob:
    def test_player_applies_successfully(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business)
            db.flush()
            applicant = _make_player(db, city, "applicant")
            job = db.query(Job).filter(Job.business_id == business.id).first()
            result = apply_for_job(db, job, applicant)
            db.flush()
            assert result["success"] is True
            assert job.filled_by_player_id == applicant.id
        finally:
            db.close()

    def test_applied_to_filled_vacancy_fails(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business)
            db.flush()
            p1 = _make_player(db, city, "p1")
            p2 = _make_player(db, city, "p2")
            job = db.query(Job).filter(Job.business_id == business.id).first()
            apply_for_job(db, job, p1)
            db.flush()
            result = apply_for_job(db, job, p2)
            assert result["success"] is False
        finally:
            db.close()

    def test_player_with_existing_job_fails(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            b1 = _make_business(db, city, owner, "shop")
            b2 = _make_business(db, city, owner, "factory")
            post_player_vacancy(db, b1)
            post_player_vacancy(db, b2)
            db.flush()
            worker = _make_player(db, city, "worker")
            job1 = db.query(Job).filter(Job.business_id == b1.id).first()
            apply_for_job(db, job1, worker)
            db.flush()
            job2 = db.query(Job).filter(Job.business_id == b2.id).first()
            result = apply_for_job(db, job2, worker)
            assert result["success"] is False
        finally:
            db.close()

    def test_insufficient_education_fails(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "factory")
            post_player_vacancy(db, business, min_education="University")
            db.flush()
            worker = _make_player(db, city, "worker")
            worker.education_level = "High School"
            db.flush()
            job = db.query(Job).filter(Job.business_id == business.id).first()
            result = apply_for_job(db, job, worker)
            assert result["success"] is False
            assert "освіта" in result["message"].lower() or "потрібна" in result["message"].lower()
        finally:
            db.close()


# --- Fire player ---


class TestFirePlayer:
    def test_owner_fires_worker(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business)
            db.flush()
            worker = _make_player(db, city, "worker")
            job = db.query(Job).filter(Job.business_id == business.id).first()
            apply_for_job(db, job, worker)
            db.flush()
            result = fire_player(db, job, owner)
            db.flush()
            assert result["success"] is True
            assert job.filled_by_player_id is None
        finally:
            db.close()

    def test_non_owner_cannot_fire(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business)
            db.flush()
            worker = _make_player(db, city, "worker")
            stranger = _make_player(db, city, "stranger")
            job = db.query(Job).filter(Job.business_id == business.id).first()
            apply_for_job(db, job, worker)
            db.flush()
            result = fire_player(db, job, stranger)
            assert result["success"] is False
        finally:
            db.close()


# --- Owner works ---


class TestOwnerWorks:
    def test_owner_works_spends_energy(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner", energy=100)
            business = _make_business(db, city, owner, "shop")
            result = owner_works_shift(db, business, owner)
            db.flush()
            assert result["success"] is True
            assert owner.energy == 100 - DEFAULT_ENERGY_COST
        finally:
            db.close()

    def test_non_owner_cannot_work(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            stranger = _make_player(db, city, "stranger")
            business = _make_business(db, city, owner, "shop")
            result = owner_works_shift(db, business, stranger)
            assert result["success"] is False
        finally:
            db.close()

    def test_low_energy_fails(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner", energy=10)
            business = _make_business(db, city, owner, "shop")
            result = owner_works_shift(db, business, owner)
            assert result["success"] is False
        finally:
            db.close()


# --- Student vacancies ---


class TestStudentVacancies:
    def test_student_vacancies_listed_separately(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business, shift_type="day")
            post_player_vacancy(db, business, shift_type="student")
            db.flush()
            all_open = list_open_vacancies(db, city.id)
            students = list_student_vacancies(db, city.id)
            assert len(all_open) == 2
            assert len(students) == 1
            assert students[0].shift_type == "student"
        finally:
            db.close()


# --- API ---


class TestVacancyApi:
    def test_list_player_vacancies_endpoint(self):
        from backend.app.api.routes.mvp import list_player_vacancies

        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business)
            db.commit()
            result = list_player_vacancies(db)
            assert result["success"] is True
            assert len(result["data"]["vacancies"]) == 1
        finally:
            db.close()

    def test_list_student_vacancies_endpoint(self):
        from backend.app.api.routes.mvp import list_student_vacancies_endpoint

        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business, shift_type="student")
            db.commit()
            result = list_student_vacancies_endpoint(db)
            assert result["success"] is True
            assert len(result["data"]["vacancies"]) == 1
            assert result["data"]["vacancies"][0]["shift_type"] == "student"
        finally:
            db.close()

    def test_job_to_dict(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            owner = _make_player(db, city, "owner")
            business = _make_business(db, city, owner, "shop")
            post_player_vacancy(db, business, bonus_pct=Decimal("15.00"))
            db.flush()
            job = db.query(Job).filter(Job.business_id == business.id).first()
            d = job_to_dict(job, include_business=True)
            assert d["bonus_pct"] == 15.0
            assert d["shift_type"] == "day"
            assert d["is_npc_position"] is False
            assert d["business_name"] == business.name
        finally:
            db.close()
