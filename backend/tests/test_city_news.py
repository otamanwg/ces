import os
from decimal import Decimal

import pytest

from backend.app.models import Business, City, Player
from backend.app.seed import seed_initial_data
from backend.app.services.city_news import build_city_news, build_day_tick_news
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def test_city_news_is_prioritized_and_limited():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        owner = Player(
            city_id=city.id,
            username="news-owner",
            balance=Decimal("1000.00"),
            energy=100,
            mood=100,
            hunger=0,
            education_level="High School",
        )
        hungry_homeless = Player(
            city_id=city.id,
            username="news-hungry",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            hunger=80,
            education_level="High School",
        )
        db.add_all([owner, hungry_homeless])
        db.flush()

        owned_business = db.query(Business).filter(Business.type == "shop").one()
        owned_business.owner_player_id = owner.id
        db.add(
            Business(
                city_id=city.id,
                name="Тестова фабрика новин",
                type="factory",
                owner_player_id=None,
                cash_balance=Decimal("500.00"),
            )
        )
        city.inflation_rate = Decimal("2.50")
        db.commit()

        news = build_city_news(db, city, max_items=3)

        assert len(news) == 3
        assert [item["type"] for item in news] == ["needs", "housing", "inflation"]
        assert [item["severity"] for item in news] == ["warning", "warning", "watch"]
        assert [item["priority"] for item in news] == [80, 70, 60]
    finally:
        db.close()


def test_day_tick_news_keeps_tick_summary_first_and_applies_limit():
    news = build_day_tick_news(
        {
            "players_updated": 4,
            "homeless_players": 2,
            "hungry_players": 3,
        },
        max_items=2,
    )

    assert [item["type"] for item in news] == ["day_tick", "housing"]
    assert news[0]["severity"] == "info"
    assert news[0]["priority"] == 20
