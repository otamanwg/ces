"""
Phase G1 — тести динамічних метрик районів.

Покриває:
- season_service: визначення сезону, множники, плавний перехід.
- district_metrics: recalculate_district_metrics оновлює метрики і створює snapshot.
- feedback loops: pollution ↑ → happiness ↓ → crime_risk ↑ → desirability ↓.
- сезонні множники впливають на метрики (весна vs зима).
- snapshot зберігається і читається.
- get_radar_with_trend повертає 6 індексів + тренд.
- day tick інтеграція: game_day_tick оновлює метрики районів.
- API /api/districts/{id}/radar повертає дані.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import (
    City,
    CityDistrict,
    DistrictMetricSnapshot,
)
from backend.app.services.district_metrics import (
    get_radar_with_trend,
    recalculate_all_districts,
    recalculate_district_metrics,
)
from backend.app.services.season_service import (
    DAYS_PER_SEASON,
    get_season_modifiers,
    season_for_game_day,
    season_transition_factor,
)
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_city_with_district(db, *, district_code: str = "test_district") -> tuple[City, CityDistrict]:
    city = City(
        name=f"TestCity_{district_code}",
        treasury_balance=Decimal("10000.00"),
        inflation_rate=Decimal("2.5"),
        game_day=0,
    )
    db.add(city)
    db.flush()
    district = CityDistrict(
        city_id=city.id,
        code=district_code,
        name="Test District",
        zone_type="residential",
        description="Test district for Phase G1 metrics.",
        display_order=0,
        land_available_hectares=Decimal("10.00"),
        rent_level=50,
        job_supply=50,
        crime_risk=30,
        traffic=40,
        service_coverage=60,
        medical_coverage=55,
        land_value=50,
        desirability=60,
    )
    db.add(district)
    db.flush()
    return city, district


# --- season_service tests ---


class TestSeasonService:
    def test_spring_is_start_season(self):
        assert season_for_game_day(0) == "spring"
        assert season_for_game_day(1) == "spring"
        assert season_for_game_day(DAYS_PER_SEASON - 1) == "spring"

    def test_season_progression(self):
        assert season_for_game_day(DAYS_PER_SEASON) == "summer"
        assert season_for_game_day(2 * DAYS_PER_SEASON) == "autumn"
        assert season_for_game_day(3 * DAYS_PER_SEASON) == "winter"
        assert season_for_game_day(4 * DAYS_PER_SEASON) == "spring"  # wraps

    def test_spring_modifiers_are_favorable(self):
        sm = get_season_modifiers(0)
        assert sm.season == "spring"
        assert sm.desirability_delta > 0
        assert sm.power_demand_delta < 0  # less demand
        assert sm.pollution_delta < 0  # rains clean air

    def test_winter_modifiers_are_harsh(self):
        sm = get_season_modifiers(3 * DAYS_PER_SEASON + 10)
        assert sm.season == "winter"
        assert sm.power_demand_delta > 30  # heating
        assert sm.pollution_delta > 20
        assert sm.desirability_delta < 0

    def test_transition_factor_zero_outside_transition_window(self):
        assert season_transition_factor(0) == 0.0
        assert season_transition_factor(10) == 0.0

    def test_transition_factor_ramps_in_last_7_days(self):
        transition_start = DAYS_PER_SEASON - 7
        assert season_transition_factor(transition_start) == 0.0
        assert 0.0 < season_transition_factor(transition_start + 1) < 1.0
        # Last day of season: 6/7 ≈ 0.857, close to (but not yet) 1.0.
        assert season_transition_factor(DAYS_PER_SEASON - 1) > 0.8

    def test_transition_interpolates_between_seasons(self):
        # Last day of spring → factor ~1 → modifiers close to summer.
        sm = get_season_modifiers(DAYS_PER_SEASON - 1)
        assert sm.season == "spring"
        # desirability_delta should be between spring (15) and summer (5).
        assert 5.0 < sm.desirability_delta < 15.0


# --- district_metrics tests ---


class TestDistrictMetricsRecalculation:
    def test_recalculate_creates_snapshot_and_updates_district(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            snapshot = recalculate_district_metrics(db, district, game_day=0)
            db.flush()

            assert snapshot.district_id == district.id
            assert snapshot.game_day == 0
            assert snapshot.season == "spring"
            # All metrics within [0, 100].
            for attr in (
                "pollution",
                "happiness",
                "crime_risk",
                "desirability",
                "land_value",
                "power_supply",
                "water_supply",
            ):
                value = getattr(snapshot, attr)
                assert 0.0 <= value <= 100.0, f"{attr}={value} out of range"
            # Composite indices within [0, 100].
            for attr in (
                "economy_score",
                "production_score",
                "household_score",
                "commerce_score",
                "infrastructure_score",
                "social_score",
            ):
                value = getattr(snapshot, attr)
                assert 0.0 <= value <= 100.0, f"{attr}={value} out of range"
            # District fields updated in-place.
            assert district.pollution == snapshot.pollution
            assert district.happiness == snapshot.happiness
        finally:
            db.close()

    def test_snapshot_persisted_after_commit(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            recalculate_district_metrics(db, district, game_day=0)
            db.commit()

            stored = db.query(DistrictMetricSnapshot).filter_by(district_id=district.id).all()
            assert len(stored) == 1
            assert stored[0].game_day == 0
        finally:
            db.close()

    def test_recalculate_all_districts_creates_one_snapshot_per_district(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = City(
                name="MultiDistrictCity",
                treasury_balance=Decimal("10000.00"),
                inflation_rate=Decimal("2.5"),
                game_day=0,
            )
            db.add(city)
            db.flush()
            for i in range(3):
                db.add(
                    CityDistrict(
                        city_id=city.id,
                        code=f"d{i}",
                        name=f"District {i}",
                        zone_type="residential",
                        description="t",
                        display_order=i,
                        land_available_hectares=Decimal("5.00"),
                    )
                )
            db.flush()
            snapshots = recalculate_all_districts(db, city.id, game_day=1)
            db.flush()

            assert len(snapshots) == 3
            for s in snapshots:
                assert s.game_day == 1
                assert s.season == "spring"
        finally:
            db.close()


class TestFeedbackLoops:
    """Метрики взаємодіють: pollution ↑ → happiness ↓ → crime_risk ↑ → desirability ↓."""

    def test_high_pollution_lowers_happiness_and_desirability(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            # Force high pollution via high traffic + production proxy (green_space low).
            district.traffic = 90
            district.green_space = 5.0
            db.flush()
            snapshot_high = recalculate_district_metrics(db, district, game_day=0)
            db.flush()

            # Reset and compare with low pollution scenario.
            district.traffic = 10
            district.green_space = 90.0
            db.flush()
            snapshot_low = recalculate_district_metrics(db, district, game_day=1)
            db.flush()

            assert snapshot_high.pollution > snapshot_low.pollution
            assert snapshot_high.happiness < snapshot_low.happiness
            assert snapshot_high.desirability < snapshot_low.desirability
        finally:
            db.close()

    def test_high_crime_lowers_land_value(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            # Low service_coverage → high crime_risk.
            district.service_coverage = 10
            db.flush()
            snapshot_high_crime = recalculate_district_metrics(db, district, game_day=0)
            db.flush()

            district.service_coverage = 95
            db.flush()
            snapshot_low_crime = recalculate_district_metrics(db, district, game_day=1)
            db.flush()

            assert snapshot_high_crime.crime_risk > snapshot_low_crime.crime_risk
            assert snapshot_high_crime.land_value < snapshot_low_crime.land_value
        finally:
            db.close()


class TestSeasonalEffect:
    """Сезонні множники впливають на метрики."""

    def test_winter_lowers_desirability_vs_spring(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            spring = recalculate_district_metrics(db, district, game_day=0)
            db.flush()

            # Same district, but deep winter.
            winter = recalculate_district_metrics(db, district, game_day=3 * DAYS_PER_SEASON + 10)
            db.flush()

            assert spring.season == "spring"
            assert winter.season == "winter"
            assert spring.desirability > winter.desirability
            assert spring.happiness > winter.happiness
        finally:
            db.close()


class TestRadarEndpoint:
    def test_radar_returns_six_indices_and_trend(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            # Create snapshots for game_day 0..7 to have trend data.
            for day in range(8):
                recalculate_district_metrics(db, district, game_day=day)
                db.flush()
            db.commit()

            radar = get_radar_with_trend(db, district.id, trend_days=7)
            indices = radar["indices"]
            trend = radar["trend"]

            assert set(indices.keys()) == {
                "economy_score",
                "production_score",
                "household_score",
                "commerce_score",
                "infrastructure_score",
                "social_score",
            }
            for value in indices.values():
                assert 0.0 <= value <= 100.0
            assert set(trend.keys()) == set(indices.keys())
            assert radar["season"] == "spring"
            assert radar["game_day"] == 7
        finally:
            db.close()

    def test_radar_returns_neutral_defaults_when_no_snapshots(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            radar = get_radar_with_trend(db, district.id)
            assert all(v == 50.0 for v in radar["indices"].values())
            assert all(v == 0.0 for v in radar["trend"].values())
        finally:
            db.close()


class TestDayTickIntegration:
    """game_day_tick оновлює метрики районів і створює snapshot-и."""

    def test_day_tick_creates_district_metric_snapshots(self):
        from backend.app.seed import seed_initial_data
        from backend.app.services.economy import game_day_tick

        db = make_test_session(TEST_DATABASE_URL)
        try:
            seed_initial_data(db)
            city = db.query(City).one()
            before = (
                db.query(DistrictMetricSnapshot)
                .filter(DistrictMetricSnapshot.district_id.in_(
                    [d.id for d in db.query(CityDistrict).filter_by(city_id=city.id).all()]
                ))
                .count()
            )
            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True

            after = (
                db.query(DistrictMetricSnapshot)
                .filter(DistrictMetricSnapshot.district_id.in_(
                    [d.id for d in db.query(CityDistrict).filter_by(city_id=city.id).all()]
                ))
                .count()
            )
            # At least one snapshot per district should have been created.
            assert after > before
        finally:
            db.close()


class TestRadarAPI:
    """API /api/districts/{id}/radar повертає дані."""

    def test_radar_api_rejects_invalid_uuid(self):
        from fastapi.testclient import TestClient

        from backend.app.database import get_db
        from backend.main import app

        os.environ["CITY_SKIP_DB_INIT"] = "true"
        db = make_test_session(TEST_DATABASE_URL)

        def _override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = _override_get_db
        try:
            with TestClient(app) as client:
                resp = client.get("/api/districts/not-a-uuid/radar")
                assert resp.status_code == 200
                body = resp.json()
                assert body["success"] is False
                assert "невірн" in body["message"].lower() or "ідентифікатор" in body["message"].lower()
        finally:
            app.dependency_overrides.clear()
            db.close()

    def test_radar_api_returns_not_found_for_unknown_district(self):
        import uuid as uuidlib

        from fastapi.testclient import TestClient

        from backend.app.database import get_db
        from backend.main import app

        os.environ["CITY_SKIP_DB_INIT"] = "true"
        db = make_test_session(TEST_DATABASE_URL)

        def _override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = _override_get_db
        try:
            with TestClient(app) as client:
                unknown_id = str(uuidlib.uuid4())
                resp = client.get(f"/api/districts/{unknown_id}/radar")
                assert resp.status_code == 200
                body = resp.json()
                assert body["success"] is False
        finally:
            app.dependency_overrides.clear()
            db.close()

    def test_radar_api_returns_data_for_seeded_district(self):
        from fastapi.testclient import TestClient

        from backend.app.database import get_db
        from backend.main import app

        os.environ["CITY_SKIP_DB_INIT"] = "true"
        db = make_test_session(TEST_DATABASE_URL)
        city, district = _make_city_with_district(db)
        recalculate_district_metrics(db, district, game_day=0)
        db.commit()
        district_id = str(district.id)

        def _override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = _override_get_db
        try:
            with TestClient(app) as client:
                resp = client.get(f"/api/districts/{district_id}/radar")
                assert resp.status_code == 200
                body = resp.json()
                assert body["success"] is True
                data = body["data"]
                assert "indices" in data
                assert "trend" in data
                assert set(data["indices"]) == {
                    "economy_score",
                    "production_score",
                    "household_score",
                    "commerce_score",
                    "infrastructure_score",
                    "social_score",
                }
        finally:
            app.dependency_overrides.clear()
            db.close()

    def test_radar_route_function_returns_data(self):
        """Directly invoke the route function with a seeded session."""
        from backend.app.api.routes.mvp import get_district_radar

        db = make_test_session(TEST_DATABASE_URL)
        try:
            city, district = _make_city_with_district(db)
            recalculate_district_metrics(db, district, game_day=0)
            db.commit()
            result = get_district_radar(str(district.id), db)
            assert result["success"] is True
            data = result["data"]
            assert "indices" in data
            assert "trend" in data
            assert set(data["indices"]) == {
                "economy_score",
                "production_score",
                "household_score",
                "commerce_score",
                "infrastructure_score",
                "social_score",
            }
        finally:
            db.close()
