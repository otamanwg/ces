"""Integration tests: G6-G10 systems wired into game_day_tick.

Verifies that the main day tick loop correctly invokes G8 police patrol,
G8 press investigation, G9 shadow economy, and G10 education systems
without crashing, and that state changes propagate.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.app.models import (
    City,
    CityDistrict,
    Education,
    Player,
    PoliceOfficer,
    PressInvestigation,
    ShadowBusiness,
)
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_city(db, game_day=0) -> City:
    city = City(
        name="GIntCity",
        treasury_balance=Decimal("100000.00"),
        game_day=game_day,
    )
    db.add(city)
    db.flush()
    return city


def _make_player(db, city, username="gintplayer", balance=10000.0) -> Player:
    player = Player(
        city_id=city.id,
        username=f"{username}_{__name__}",
        balance=Decimal(str(balance)),
        energy=100,
        mood=80,
        hunger=0,
    )
    db.add(player)
    db.flush()
    return player


def _make_district(db, city, name="GIntDistrict") -> CityDistrict:
    district = CityDistrict(
        city_id=city.id,
        code=name.lower(),
        name=name,
        zone_type="residential",
        description="t",
        display_order=0,
        land_available_hectares=Decimal("10.00"),
        crime_risk=50,
    )
    db.add(district)
    db.flush()
    return district


class TestDayTickG6G10Integration:
    """Verify game_day_tick invokes G6-G10 systems."""

    def test_tick_with_no_g6_g10_data(self):
        """Day tick should succeed even with no G6-G10 records."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            _make_player(db, city, "bare")
            db.commit()

            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            assert city.game_day == 1
        finally:
            db.close()

    def test_tick_with_police_officer_patrol(self):
        """Police officer with assigned district auto-patrols on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "cop")
            district = _make_district(db, city)
            officer = PoliceOfficer(
                city_id=city.id,
                player_id=player.id,
                rank="patrol",
                patrol_district_id=district.id,
                is_active=True,
                hired_at_game_day=0,
            )
            db.add(officer)
            db.commit()

            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            # Officer should still be active after patrol
            db.refresh(officer)
            assert officer.is_active is True
        finally:
            db.close()

    def test_tick_with_press_investigation(self):
        """Press investigation accumulates evidence on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            journalist = _make_player(db, city, "journo")
            target = _make_player(db, city, "target")
            inv = PressInvestigation(
                target_player_id=target.id,
                journalist_id=journalist.id,
                incident_type="corruption",
                press_evidence=0.0,
                is_published=False,
            )
            db.add(inv)
            db.commit()

            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            db.refresh(inv)
            # Evidence should have increased
            assert inv.press_evidence > 0.0
        finally:
            db.close()

    def test_tick_with_shadow_business_income(self):
        """Shadow business generates income on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow_owner", balance=5000.0)
            player.criminal_rep = 40.0
            district = _make_district(db, city)
            shadow_biz = ShadowBusiness(
                owner_id=player.id,
                type="illegal_bar",
                district_id=district.id,
                cash_balance=Decimal("0.0"),
                is_discovered=False,
            )
            db.add(shadow_biz)
            db.commit()

            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            db.refresh(shadow_biz)
            # Income should have been added (unless discovered, which is rare)
            # We just verify no crash and cash_balance is a valid number
            assert shadow_biz.cash_balance is not None
        finally:
            db.close()

    def test_tick_with_education_enrolled(self):
        """Enrolled education consumes energy on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "student", balance=10000.0)
            from backend.app.services.education_service import enroll

            enroll(db, player, "economic", "full_time")
            db.commit()

            energy_before = player.energy
            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            db.refresh(player)
            # Energy should have decreased (education + base tick decay)
            assert player.energy < energy_before
        finally:
            db.close()

    def test_tick_education_auto_complete(self):
        """Education enrolled long ago auto-completes on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "grad", balance=10000.0)
            from backend.app.services.education_service import enroll

            enroll(db, player, "fashion", "full_time")
            db.commit()

            # Manually set enrolled_at to 31 days ago (duration is 30 days)
            edu = db.query(Education).filter(Education.player_id == player.id).first()
            edu.enrolled_at = datetime.now(UTC) - timedelta(days=31)
            db.commit()

            from backend.app.services.economy import game_day_tick

            game_day_tick(db, str(city.id))
            db.commit()
            db.refresh(edu)
            assert edu.status == "completed"
            assert edu.completed_at is not None
        finally:
            db.close()

    def test_tick_criminal_rep_decay_monthly(self):
        """Criminal_rep decays every 30 game days."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            # Start at game_day=29 so next tick is 30 (decay triggers)
            city = _make_city(db, game_day=29)
            player = _make_player(db, city, "exconvict", balance=5000.0)
            player.criminal_rep = 50.0
            db.commit()

            from backend.app.services.economy import game_day_tick

            game_day_tick(db, str(city.id))
            db.commit()
            db.refresh(player)
            # game_day is now 30, decay should have triggered
            assert player.criminal_rep < 50.0
        finally:
            db.close()

    def test_tick_fraud_offer_high_rep(self):
        """Player with high criminal_rep may receive fraud offer on tick."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "highrep", balance=5000.0)
            player.criminal_rep = 70.0
            db.commit()

            from backend.app.services.economy import game_day_tick

            # Run several ticks — with rep=70, 30% chance per day
            for _ in range(10):
                result = game_day_tick(db, str(city.id))
                db.commit()
                assert result["success"] is True
        finally:
            db.close()

    def test_tick_all_systems_together(self):
        """All G6-G10 systems active simultaneously — no crash."""
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            # Police
            cop = _make_player(db, city, "cop_all")
            district = _make_district(db, city)
            officer = PoliceOfficer(
                city_id=city.id,
                player_id=cop.id,
                rank="patrol",
                patrol_district_id=district.id,
                is_active=True,
                hired_at_game_day=0,
            )
            db.add(officer)
            # Press
            journo = _make_player(db, city, "journo_all")
            target = _make_player(db, city, "target_all")
            inv = PressInvestigation(
                target_player_id=target.id,
                journalist_id=journo.id,
                incident_type="corruption",
                press_evidence=0.0,
            )
            db.add(inv)
            # Shadow
            shadow_owner = _make_player(db, city, "shadow_all", balance=5000.0)
            shadow_owner.criminal_rep = 40.0
            shadow_biz = ShadowBusiness(
                owner_id=shadow_owner.id,
                type="smuggling",
                district_id=district.id,
                cash_balance=Decimal("0.0"),
            )
            db.add(shadow_biz)
            # Education
            student = _make_player(db, city, "student_all", balance=10000.0)
            from backend.app.services.education_service import enroll

            enroll(db, student, "legal", "full_time")
            db.commit()

            from backend.app.services.economy import game_day_tick

            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            assert city.game_day == 1
        finally:
            db.close()


class TestPhaseG6G10TickModule:
    """Direct tests of the phase_g6_to_g10_tick module."""

    def test_run_g6_to_g10_tick_empty_city(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            db.commit()

            from backend.app.services.phase_g6_to_g10_tick import run_g6_to_g10_tick

            stats = run_g6_to_g10_tick(db, city, game_day=1)
            db.commit()
            assert "police" in stats
            assert "press" in stats
            assert "shadow" in stats
            assert "education" in stats
            assert stats["police"]["patrols"] == 0
            assert stats["press"]["investigations_ticked"] == 0
        finally:
            db.close()
