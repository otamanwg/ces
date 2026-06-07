"""
Тести для системи управління бізнесом (AI/manual/shadow) та daily revenue.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Business, City, Player
from backend.app.services.business_management import (
    get_business_tier,
    switch_management_mode,
    update_business_size,
)
from backend.app.services.daily_business_revenue import (
    _competition_modifier_from_count,
    calculate_market_competition_modifier,
    process_all_businesses_daily_revenue,
    process_daily_business_revenue,
)
from backend.app.services.money import money


class TestBusinessTier:
    """Тести рівнів бізнесу."""

    def test_tier_micro(self):
        assert get_business_tier(1) == "micro"
        assert get_business_tier(5) == "micro"

    def test_tier_small(self):
        assert get_business_tier(6) == "small"
        assert get_business_tier(50) == "small"

    def test_tier_medium(self):
        assert get_business_tier(51) == "medium"
        assert get_business_tier(200) == "medium"

    def test_tier_large(self):
        assert get_business_tier(201) == "large"
        assert get_business_tier(1000) == "large"

    def test_tier_mega(self):
        assert get_business_tier(1001) == "mega"


class TestCompetitionModifier:
    """Тести модифікатора конкуренції."""

    def test_monopoly_bonus(self):
        assert _competition_modifier_from_count(0) == 1.2

    def test_normal_competition(self):
        assert _competition_modifier_from_count(1) == 1.0
        assert _competition_modifier_from_count(2) == 1.0

    def test_high_competition(self):
        assert _competition_modifier_from_count(3) == 0.8
        assert _competition_modifier_from_count(5) == 0.8

    def test_saturation(self):
        assert _competition_modifier_from_count(6) == 0.6
        assert _competition_modifier_from_count(20) == 0.6


class TestBusinessManagementService:
    """Інтеграційні тести сервісу управління бізнесом."""

    @pytest.fixture
    def db_session(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.rollback()
            db.close()

    @pytest.fixture
    def city_and_player(self, db_session: Session):
        city = db_session.query(City).first()
        assert city is not None, "Потрібне місто у БД"
        player = db_session.query(Player).first()
        assert player is not None, "Потрібен гравець у БД"
        return city, player

    @pytest.fixture
    def ai_business(self, db_session: Session, city_and_player):
        city, player = city_and_player
        b = Business(
            name=f"TestBiz-{uuid.uuid4().hex[:6]}",
            type="shop",
            city_id=city.id,
            owner_player_id=player.id,
            management_mode="ai",
            business_size=2,
            cash_balance=money("5000.00"),
            status="active",
        )
        db_session.add(b)
        db_session.flush()
        yield b
        db_session.delete(b)
        db_session.commit()

    def test_switch_mode_ai_to_manual(self, db_session: Session, ai_business: Business):
        result = switch_management_mode(db_session, ai_business, "manual")
        assert result["success"] is True
        assert ai_business.management_mode == "manual"

    def test_switch_mode_invalid(self, db_session: Session, ai_business: Business):
        result = switch_management_mode(db_session, ai_business, "invalid")
        assert result["success"] is False

    def test_update_business_size(self, db_session: Session, ai_business: Business):
        result = update_business_size(db_session, ai_business, 5)
        assert result["success"] is True
        assert ai_business.business_size == 5

    def test_update_size_zero_blocks_revenue(self, db_session: Session, ai_business: Business):
        update_business_size(db_session, ai_business, 0)
        db_session.flush()
        result = process_daily_business_revenue(db_session, ai_business)
        assert result["success"] is False

    def test_daily_revenue_skips_inactive(self, db_session: Session, ai_business: Business):
        ai_business.status = "inactive"
        db_session.flush()
        result = process_daily_business_revenue(db_session, ai_business)
        assert result["success"] is False

    def test_daily_revenue_skips_zero_size(self, db_session: Session, ai_business: Business):
        ai_business.business_size = 0
        db_session.flush()
        result = process_daily_business_revenue(db_session, ai_business)
        assert result["success"] is False

    def test_daily_revenue_ai_mode(self, db_session: Session, ai_business: Business):
        initial_balance = Decimal(str(ai_business.cash_balance))
        result = process_daily_business_revenue(db_session, ai_business)
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["net_profit"] > 0
        assert Decimal(str(ai_business.cash_balance)) > initial_balance

    def test_competition_cache_used(self, db_session: Session, ai_business: Business):
        cache = {"shop": 1}
        result = calculate_market_competition_modifier(db_session, ai_business, competition_cache=cache)
        assert result == 1.2

    def test_process_all_filters_ai_only(self, db_session: Session, city_and_player):
        city, player = city_and_player
        manual_biz = Business(
            name=f"ManualBiz-{uuid.uuid4().hex[:6]}",
            type="shop",
            city_id=city.id,
            owner_player_id=player.id,
            management_mode="manual",
            business_size=1,
            cash_balance=money("1000.00"),
            status="active",
        )
        db_session.add(manual_biz)
        db_session.flush()

        initial_balance = Decimal(str(manual_biz.cash_balance))
        process_all_businesses_daily_revenue(db_session, city.id)
        db_session.refresh(manual_biz)

        assert Decimal(str(manual_biz.cash_balance)) == initial_balance

        db_session.delete(manual_biz)
        db_session.commit()
