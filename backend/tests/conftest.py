"""Shared pytest fixtures for backend integration tests.

Provides a fresh PostgreSQL session (schema reset + Alembic upgrade per test)
and default domain entities (City, Player, CityDistrict, Business) to reduce
boilerplate across the G5-G10 service test suites.

The ``db`` fixture drops and recreates the public schema on every test, matching
the previous per-test ``make_test_session`` usage. Entity fixtures depend on
``db`` so they always operate on the freshly migrated schema.

Unique usernames are derived from ``request.node.name`` so the default ``player``
fixture never collides with additional players created by local helpers within
the same test (the schema is reset between tests, so cross-test collisions are
not a concern).
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import Business, City, CityDistrict, Player
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")


@pytest.fixture()
def db():
    """Yield a fresh SQLAlchemy session on a reset + migrated test database."""
    session = make_test_session(TEST_DATABASE_URL)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def city(db) -> City:
    """Default City: treasury_balance=100000.00, game_day=0."""
    city = City(
        name="TestCity",
        treasury_balance=Decimal("100000.00"),
        game_day=0,
    )
    db.add(city)
    db.flush()
    return city


@pytest.fixture()
def player(db, city, request) -> Player:
    """Default Player in city: balance=5000.0, energy=100, mood=80, hunger=0."""
    raw = request.node.name.replace("[", "_").replace("]", "_")
    username = f"fx_{raw}"[:45]
    player = Player(
        city_id=city.id,
        username=username,
        balance=Decimal("5000.0"),
        energy=100,
        mood=80,
        hunger=0,
    )
    db.add(player)
    db.flush()
    return player


@pytest.fixture()
def district(db, city) -> CityDistrict:
    """Default CityDistrict in city: crime_risk=50."""
    district = CityDistrict(
        city_id=city.id,
        code="testdistrict",
        name="TestDistrict",
        zone_type="residential",
        description="t",
        display_order=0,
        land_available_hectares=Decimal("10.00"),
        crime_risk=50,
    )
    db.add(district)
    db.flush()
    return district


@pytest.fixture()
def business(db, city, player) -> Business:
    """Default Business in city owned by player: type='shop', cash_balance=10000.0."""
    biz = Business(
        city_id=city.id,
        name="TestShop",
        type="shop",
        owner_player_id=player.id,
        cash_balance=Decimal("10000.0"),
        status="active",
    )
    db.add(biz)
    db.flush()
    return biz
