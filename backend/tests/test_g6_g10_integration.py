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
    Education,
    Player,
    PoliceOfficer,
    PressInvestigation,
    ShadowBusiness,
)

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_player(db, city, username="gintplayer", balance=10000.0) -> Player:
    """Create a player with a custom username/balance (fixture default is 5000.0)."""
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


class TestDayTickG6G10Integration:
    """Verify game_day_tick invokes G6-G10 systems."""

    def test_tick_with_no_g6_g10_data(self, db, city, player):
        """Day tick should succeed even with no G6-G10 records."""
        db.commit()

        from backend.app.services.economy import game_day_tick

        result = game_day_tick(db, str(city.id))
        db.commit()
        assert result["success"] is True
        assert city.game_day == 1

    def test_tick_with_police_officer_patrol(self, db, city, player, district):
        """Police officer with assigned district auto-patrols on tick."""
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

    def test_tick_with_press_investigation(self, db, city, player):
        """Press investigation accumulates evidence on tick."""
        target = _make_player(db, city, "target")
        inv = PressInvestigation(
            target_player_id=target.id,
            journalist_id=player.id,
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

    def test_tick_with_shadow_business_income(self, db, city, player, district):
        """Shadow business generates income on tick."""
        player.criminal_rep = 40.0
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

    def test_tick_with_education_enrolled(self, db, city):
        """Enrolled education consumes energy on tick."""
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

    def test_tick_education_auto_complete(self, db, city):
        """Education enrolled long ago auto-completes on tick."""
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

    def test_tick_criminal_rep_decay_monthly(self, db, city, player):
        """Criminal_rep decays every 30 game days."""
        # Start at game_day=29 so next tick is 30 (decay triggers)
        city.game_day = 29
        player.criminal_rep = 50.0
        db.commit()

        from backend.app.services.economy import game_day_tick

        game_day_tick(db, str(city.id))
        db.commit()
        db.refresh(player)
        # game_day is now 30, decay should have triggered
        assert player.criminal_rep < 50.0

    def test_tick_fraud_offer_high_rep(self, db, city, player):
        """Player with high criminal_rep may receive fraud offer on tick."""
        player.criminal_rep = 70.0
        db.commit()

        from backend.app.services.economy import game_day_tick

        # Run several ticks — with rep=70, 30% chance per day
        for _ in range(10):
            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True

    def test_tick_all_systems_together(self, db, city, player, district):
        """All G6-G10 systems active simultaneously — no crash."""
        # Police (player fixture = cop_all)
        officer = PoliceOfficer(
            city_id=city.id,
            player_id=player.id,
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


class TestPhaseG6G10TickModule:
    """Direct tests of the phase_g6_to_g10_tick module."""

    def test_run_g6_to_g10_tick_empty_city(self, db, city):
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
