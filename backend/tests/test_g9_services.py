"""
Phase G9 — тести казино, ательє, тіньових ніш.

Покриває:
- Casino: blackjack, roulette, poker create/settle, tax, license fee, shutdown.
- Atelier: create skin, buy skin, equip/unequip, list for sale, price calc.
- Shadow: criminal_rep add/decay, open shadow business, income, discovery,
  fraud offer/accept/refuse, money laundering, shadow market buy/sell.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import (
    Business,
    CasinoGame,
    City,
    CityDistrict,
    CriminalRepLog,
    Player,
    PlayerSkin,
    ShadowBusiness,
    Skin,
)
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_city(db) -> City:
    city = City(name="G9TestCity", treasury_balance=Decimal("100000.00"), game_day=0)
    db.add(city)
    db.flush()
    return city


def _make_player(db, city, username="g9player", balance=5000.0) -> Player:
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


def _make_district(db, city, name="G9District") -> CityDistrict:
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


def _make_business(db, city, owner, btype="casino", cash=20000.0, name="G9Biz") -> Business:
    biz = Business(
        city_id=city.id,
        name=f"{name}_{btype}_{__name__}",
        type=btype,
        owner_player_id=owner.id,
        cash_balance=Decimal(str(cash)),
        status="active",
    )
    db.add(biz)
    db.flush()
    return biz


# --- Casino ---


class TestCasino:
    def test_blackjack_win_or_loss(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "bj", balance=1000.0)
            casino = _make_business(db, city, player, "casino", cash=50000.0)
            from backend.app.services.casino_service import play_blackjack

            result = play_blackjack(db, casino, player, Decimal("100"))
            db.flush()
            assert result["success"] is True
            assert "won" in result
        finally:
            db.close()

    def test_blackjack_insufficient_balance(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "bj2", balance=50.0)
            casino = _make_business(db, city, player, "casino", cash=50000.0)
            from backend.app.services.casino_service import play_blackjack

            result = play_blackjack(db, casino, player, Decimal("100"))
            assert result["success"] is False
        finally:
            db.close()

    def test_roulette_red_black(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "roul", balance=1000.0)
            casino = _make_business(db, city, player, "casino", cash=50000.0)
            from backend.app.services.casino_service import play_roulette

            result = play_roulette(db, casino, player, Decimal("100"), "red")
            db.flush()
            assert result["success"] is True
        finally:
            db.close()

    def test_roulette_number_payout(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "roul2", balance=1000.0)
            casino = _make_business(db, city, player, "casino", cash=100000.0)
            from backend.app.services.casino_service import play_roulette

            # Run many times to verify no crash on number bet
            for _ in range(5):
                result = play_roulette(db, casino, player, Decimal("10"), "number")
                db.flush()
                assert result["success"] is True
        finally:
            db.close()

    def test_poker_create(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "poker", balance=5000.0)
            casino = _make_business(db, city, player, "casino", cash=50000.0)
            from backend.app.services.casino_service import create_poker_game

            result = create_poker_game(db, casino, Decimal("100"))
            db.flush()
            assert result["success"] is True
            assert "game_id" in result
            game = db.query(CasinoGame).filter(CasinoGame.id == result["game_id"]).first()
            assert game is not None
            assert game.game_type == "poker"
            assert game.status == "waiting"
        finally:
            db.close()

    def test_casino_tax_collection(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "ctax", balance=5000.0)
            casino = _make_business(db, city, player, "casino", cash=50000.0)
            casino.daily_revenue = Decimal("1000.00")
            db.flush()
            from backend.app.services.casino_service import collect_casino_tax

            treasury_before = city.treasury_balance
            result = collect_casino_tax(db, casino, city)
            db.flush()
            assert result["success"] is True
            assert city.treasury_balance > treasury_before
        finally:
            db.close()

    def test_casino_license_fee(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "clic", balance=5000.0)
            casino = _make_business(db, city, player, "casino", cash=5000.0)
            from backend.app.services.casino_service import pay_license_fee

            treasury_before = city.treasury_balance
            result = pay_license_fee(db, casino, city)
            db.flush()
            assert result["success"] is True
            assert city.treasury_balance > treasury_before
        finally:
            db.close()

    def test_casino_shutdown(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "cshut", balance=5000.0)
            casino = _make_business(db, city, player, "casino", cash=5000.0)
            from backend.app.services.casino_service import shut_down_casino

            result = shut_down_casino(db, casino, "license revoked")
            db.flush()
            assert result["success"] is True
            assert casino.status != "active"
        finally:
            db.close()


# --- Atelier ---


class TestAtelier:
    def test_create_skin_common(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "designer", balance=5000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import create_skin

            result = create_skin(
                db,
                designer,
                atelier,
                "Test Skin",
                {"hair": "black", "suit": "blue"},
                "common",
                False,
                10,
                Decimal("100"),
            )
            db.flush()
            assert result["success"] is True
            skin = db.query(Skin).filter(Skin.id == result["skin_id"]).first()
            assert skin is not None
            assert skin.rarity == "common"
            assert skin.is_unique is False
        finally:
            db.close()

    def test_create_skin_unique_forces_one_copy(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "designer2", balance=5000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import create_skin

            result = create_skin(
                db,
                designer,
                atelier,
                "Unique Skin",
                {"hair": "gold"},
                "legendary",
                True,
                99,  # should be forced to 1
                Decimal("25000"),
            )
            db.flush()
            skin = db.query(Skin).filter(Skin.id == result["skin_id"]).first()
            assert skin.copies_total == 1
        finally:
            db.close()

    def test_create_skin_invalid_rarity(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "designer3", balance=5000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import create_skin

            result = create_skin(db, designer, atelier, "Bad", {}, "mythic", False, 1, Decimal("100"))
            assert result["success"] is False
        finally:
            db.close()

    def test_buy_skin(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "seller", balance=5000.0)
            buyer = _make_player(db, city, "buyer", balance=10000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import buy_skin, create_skin

            skin_result = create_skin(
                db, designer, atelier, "For Sale", {"hair": "red"}, "rare", False, 5, Decimal("300")
            )
            db.flush()
            skin = db.query(Skin).filter(Skin.id == skin_result["skin_id"]).first()
            result = buy_skin(db, buyer, skin, atelier)
            db.flush()
            assert result["success"] is True
            ps = db.query(PlayerSkin).filter(PlayerSkin.id == result["player_skin_id"]).first()
            assert ps is not None
            assert skin.copies_sold == 1
        finally:
            db.close()

    def test_buy_skin_insufficient_balance(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "seller2", balance=5000.0)
            buyer = _make_player(db, city, "poorbuyer", balance=10.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import buy_skin, create_skin

            skin_result = create_skin(db, designer, atelier, "Expensive", {}, "epic", False, 1, Decimal("1000"))
            db.flush()
            skin = db.query(Skin).filter(Skin.id == skin_result["skin_id"]).first()
            result = buy_skin(db, buyer, skin, atelier)
            assert result["success"] is False
        finally:
            db.close()

    def test_equip_skin(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "seller3", balance=5000.0)
            buyer = _make_player(db, city, "buyer3", balance=10000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import (
                buy_skin,
                create_skin,
                equip_skin,
            )

            skin_result = create_skin(db, designer, atelier, "Equip Me", {}, "common", False, 5, Decimal("100"))
            db.flush()
            skin = db.query(Skin).filter(Skin.id == skin_result["skin_id"]).first()
            buy_result = buy_skin(db, buyer, skin, atelier)
            db.flush()
            ps = db.query(PlayerSkin).filter(PlayerSkin.id == buy_result["player_skin_id"]).first()
            result = equip_skin(db, buyer, ps)
            db.flush()
            assert result["success"] is True
            assert ps.is_equipped is True
        finally:
            db.close()

    def test_list_skins_for_sale(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            designer = _make_player(db, city, "seller4", balance=5000.0)
            atelier = _make_business(db, city, designer, "atelier", cash=5000.0)
            from backend.app.services.atelier_service import create_skin, list_skins_for_sale

            create_skin(db, designer, atelier, "S1", {}, "common", False, 5, Decimal("100"))
            create_skin(db, designer, atelier, "S2", {}, "rare", False, 3, Decimal("300"))
            db.flush()
            skins = list_skins_for_sale(db, atelier)
            assert len(skins) == 2
        finally:
            db.close()

    def test_calculate_skin_price(self):
        from backend.app.services.atelier_service import calculate_skin_price

        assert calculate_skin_price("common", False) == Decimal("100.00")
        assert calculate_skin_price("rare", False) == Decimal("300.00")
        assert calculate_skin_price("epic", False) == Decimal("1000.00")
        assert calculate_skin_price("legendary", False) == Decimal("5000.00")
        assert calculate_skin_price("legendary", True) == Decimal("25000.00")


# --- Shadow ---


class TestShadow:
    def test_add_criminal_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "crep", balance=5000.0)
            from backend.app.services.shadow_service import add_criminal_rep

            result = add_criminal_rep(db, player, 20.0, "prison_sentence")
            db.flush()
            assert result["success"] is True
            assert result["new_rep"] == 20.0
            log = db.query(CriminalRepLog).filter(CriminalRepLog.player_id == player.id).first()
            assert log is not None
        finally:
            db.close()

    def test_criminal_rep_clamped_to_100(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "crep2", balance=5000.0)
            from backend.app.services.shadow_service import add_criminal_rep

            add_criminal_rep(db, player, 90.0, "big_crime")
            result = add_criminal_rep(db, player, 50.0, "more_crime")
            db.flush()
            assert result["new_rep"] == 100.0
        finally:
            db.close()

    def test_criminal_rep_clamped_to_0(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "crep3", balance=5000.0)
            from backend.app.services.shadow_service import add_criminal_rep

            result = add_criminal_rep(db, player, -50.0, "negative_test")
            db.flush()
            assert result["new_rep"] == 0.0
        finally:
            db.close()

    def test_decay_criminal_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "crep4", balance=5000.0)
            from backend.app.services.shadow_service import add_criminal_rep, decay_criminal_rep

            add_criminal_rep(db, player, 30.0, "initial")
            result = decay_criminal_rep(db, player)
            db.flush()
            assert result["success"] is True
            assert result["new_rep"] == 29.0
        finally:
            db.close()

    def test_can_access_shadow_market(self):
        from backend.app.services.shadow_service import can_access_shadow_market

        class FakeP:
            criminal_rep = 30.0

        assert can_access_shadow_market(FakeP()) is True

        class FakeP2:
            criminal_rep = 29.9

        assert can_access_shadow_market(FakeP2()) is False

    def test_open_shadow_business_requires_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow1", balance=5000.0)
            district = _make_district(db, city)
            from backend.app.services.shadow_service import open_shadow_business

            result = open_shadow_business(db, player, district, "illegal_bar")
            assert result["success"] is False  # criminal_rep = 0
        finally:
            db.close()

    def test_open_shadow_business_with_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow2", balance=5000.0)
            district = _make_district(db, city)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                open_shadow_business,
            )

            add_criminal_rep(db, player, 35.0, "ex_convict")
            db.flush()
            result = open_shadow_business(db, player, district, "smuggling")
            db.flush()
            assert result["success"] is True
            biz = db.query(ShadowBusiness).filter(ShadowBusiness.id == result["business_id"]).first()
            assert biz is not None
            assert biz.type == "smuggling"
            assert biz.is_discovered is False
        finally:
            db.close()

    def test_open_shadow_business_invalid_type(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow3", balance=5000.0)
            district = _make_district(db, city)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                open_shadow_business,
            )

            add_criminal_rep(db, player, 50.0, "ex_convict")
            db.flush()
            result = open_shadow_business(db, player, district, "human_trafficking")
            assert result["success"] is False
        finally:
            db.close()

    def test_shadow_business_income(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow4", balance=5000.0)
            district = _make_district(db, city)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                open_shadow_business,
                shadow_business_income,
            )

            add_criminal_rep(db, player, 40.0, "ex_convict")
            db.flush()
            biz_result = open_shadow_business(db, player, district, "money_laundering")
            db.flush()
            biz = db.query(ShadowBusiness).filter(ShadowBusiness.id == biz_result["business_id"]).first()
            cash_before = biz.cash_balance
            result = shadow_business_income(db, biz, game_day=1)
            db.flush()
            assert result["success"] is True
            assert biz.cash_balance > cash_before
        finally:
            db.close()

    def test_check_discovery_no_discovery(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "shadow5", balance=5000.0)
            district = _make_district(db, city)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                check_discovery,
                open_shadow_business,
            )

            add_criminal_rep(db, player, 30.0, "ex_convict")
            db.flush()
            biz_result = open_shadow_business(db, player, district, "illegal_bar")
            db.flush()
            biz = db.query(ShadowBusiness).filter(ShadowBusiness.id == biz_result["business_id"]).first()
            # Run many times; with rep=30, chance = 0.05 + 30*0.003 = 0.14
            # We just verify no crash and structure correct
            for _ in range(10):
                result = check_discovery(db, biz, player)
                db.flush()
                assert "discovered" in result
                if result["discovered"]:
                    assert biz.is_discovered is True
                    break
        finally:
            db.close()

    def test_offer_fraud_low_rep_no_offer(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "fraud1", balance=5000.0)
            from backend.app.services.shadow_service import offer_fraud

            # criminal_rep = 0 → 0% chance
            for _ in range(20):
                result = offer_fraud(db, player, game_day=1)
                assert result["offered"] is False
        finally:
            db.close()

    def test_accept_fraud(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "fraud2", balance=5000.0)
            from backend.app.services.shadow_service import accept_fraud

            balance_before = player.balance
            result = accept_fraud(db, player, Decimal("500"), game_day=1)
            db.flush()
            assert result["success"] is True
            assert player.balance > balance_before
            assert player.criminal_rep > 0
        finally:
            db.close()

    def test_refuse_fraud(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "fraud3", balance=5000.0)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                refuse_fraud,
            )

            add_criminal_rep(db, player, 20.0, "initial")
            db.flush()
            rep_before = player.criminal_rep
            result = refuse_fraud(db, player)
            db.flush()
            assert result["success"] is True
            assert player.criminal_rep < rep_before
        finally:
            db.close()

    def test_money_laundering(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            launderer = _make_player(db, city, "launderer", balance=10000.0)
            client = _make_player(db, city, "client", balance=1000.0)
            from backend.app.services.shadow_service import money_laundering_service

            result = money_laundering_service(db, launderer, client, Decimal("1000"))
            db.flush()
            assert result["success"] is True
            assert "commission" in result
            assert launderer.criminal_rep > 0
            assert client.criminal_rep > 0
        finally:
            db.close()

    def test_shadow_market_buy_requires_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "market1", balance=5000.0)
            from backend.app.services.shadow_service import shadow_market_buy

            result = shadow_market_buy(db, player, "electronics", 5)
            assert result["success"] is False  # criminal_rep = 0
        finally:
            db.close()

    def test_shadow_market_buy_with_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "market2", balance=5000.0)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                shadow_market_buy,
            )

            add_criminal_rep(db, player, 40.0, "ex_convict")
            db.flush()
            balance_before = player.balance
            result = shadow_market_buy(db, player, "electronics", 2)
            db.flush()
            assert result["success"] is True
            assert player.balance < balance_before
        finally:
            db.close()

    def test_shadow_market_sell_with_rep(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            player = _make_player(db, city, "market3", balance=5000.0)
            from backend.app.services.shadow_service import (
                add_criminal_rep,
                shadow_market_sell,
            )

            add_criminal_rep(db, player, 40.0, "ex_convict")
            db.flush()
            balance_before = player.balance
            result = shadow_market_sell(db, player, "alcohol", 3)
            db.flush()
            assert result["success"] is True
            assert player.balance > balance_before
        finally:
            db.close()
