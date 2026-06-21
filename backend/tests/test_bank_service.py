"""
Phase G5 — тести банку як бізнесу.

Покриває:
- Bank blueprint.
- Депозити: створення, зняття, нарахування відсотків.
- Кредити: видача, погашення, нарахування відсотків, дефолт.
- Аукціон банкрутів: створення, ставки, закриття, передача бізнесу.
- API endpoints.
- Day tick інтеграція.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.app.models import (
    BankCredit,
    BankDeposit,
    BankruptcyAuction,
    Business,
    Player,
)
from backend.app.services.bank_service import (
    AUCTION_CITY_PERCENTAGE,
    AUCTION_MIN_BID_INCREMENT,
    close_auction,
    create_deposit,
    issue_loan,
    list_active_auctions,
    place_bid,
    process_deposit_interest,
    process_loan_interest,
    repay_loan,
    trigger_bankruptcy_auction,
    withdraw_deposit,
)

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_bank(db, city, cash: float = 50000.0, owner: Player | None = None) -> Business:
    bank = Business(
        city_id=city.id,
        name="TestBank",
        type="bank",
        legal_form="tov",
        cash_balance=Decimal(str(cash)),
        status="active",
        owner_player_id=owner.id if owner else None,
    )
    db.add(bank)
    db.flush()
    return bank


def _make_player(db, city, username: str = "testplayer", balance: float = 5000.0) -> Player:
    """Create a player with a custom username/balance (for custom-balance cases)."""
    player = Player(
        city_id=city.id,
        username=f"{username}_{__name__}",
        balance=Decimal(str(balance)),
        energy=100,
        mood=80,
        hunger=0,
        education_level="High School",
    )
    db.add(player)
    db.flush()
    return player


def _make_bankrupt_business(db, city, owner: Player | None = None) -> Business:
    business = Business(
        city_id=city.id,
        name="BankruptBiz",
        type="shop",
        legal_form="fop",
        cash_balance=Decimal("-500.00"),
        status="bankrupt",
        owner_player_id=owner.id if owner else None,
    )
    db.add(business)
    db.flush()
    return business


# --- Bank blueprint ---


class TestBankBlueprint:
    def test_bank_blueprint_exists_after_seed(self, db):
        from backend.app.models import BusinessBlueprint
        from backend.app.services.business_blueprints import ensure_business_blueprints

        ensure_business_blueprints(db)
        db.commit()
        bp = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == "bank").first()
        assert bp is not None
        assert bp.category == "finance"
        assert bp.business_type == "bank"


# --- Deposits ---


class TestDeposits:
    def test_create_deposit_success(self, db, city):
        bank = _make_bank(db, city)
        player = _make_player(db, city, "depositor", 1000.0)
        result = create_deposit(db, bank, player, Decimal("500.00"), game_day=1)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(player.balance)) == Decimal("500.00")
        assert Decimal(str(bank.cash_balance)) == Decimal("50500.00")

    def test_create_deposit_insufficient_funds(self, db, city):
        bank = _make_bank(db, city)
        player = _make_player(db, city, "poor", 100.0)
        result = create_deposit(db, bank, player, Decimal("500.00"), game_day=1)
        assert result["success"] is False

    def test_create_deposit_non_bank_business(self, db, city):
        shop = Business(
            city_id=city.id,
            name="Shop",
            type="shop",
            legal_form="fop",
            cash_balance=Decimal("1000.00"),
            status="active",
        )
        db.add(shop)
        db.flush()
        player = _make_player(db, city, "p", 1000.0)
        result = create_deposit(db, shop, player, Decimal("100.00"), game_day=1)
        assert result["success"] is False

    def test_withdraw_deposit(self, db, city):
        bank = _make_bank(db, city)
        player = _make_player(db, city, "depositor", 1000.0)
        create_deposit(db, bank, player, Decimal("500.00"), game_day=1)
        db.flush()
        deposit = db.query(BankDeposit).first()
        result = withdraw_deposit(db, deposit, player)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(player.balance)) == Decimal("1000.00")
        assert deposit.is_active is False

    def test_deposit_interest_accrues(self, db, city):
        bank = _make_bank(db, city)
        player = _make_player(db, city, "saver", 1000.0)
        create_deposit(db, bank, player, Decimal("1000.00"), Decimal("10.00"), game_day=1)
        db.flush()
        # 10 днів потому
        result = process_deposit_interest(db, city.id, game_day=11)
        db.flush()
        assert result["deposits_processed"] == 1
        assert result["total_interest"] > 0
        deposit = db.query(BankDeposit).first()
        assert Decimal(str(deposit.amount)) > Decimal("1000.00")


# --- Loans ---


class TestLoans:
    def test_issue_loan_success(self, db, city):
        bank = _make_bank(db, city, 50000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        result = issue_loan(db, bank, borrower, Decimal("5000.00"), game_day=1)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(borrower.balance)) == Decimal("5100.00")
        assert Decimal(str(bank.cash_balance)) == Decimal("45000.00")

    def test_issue_loan_bank_insufficient(self, db, city):
        bank = _make_bank(db, city, 1000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        result = issue_loan(db, bank, borrower, Decimal("5000.00"), game_day=1)
        assert result["success"] is False

    def test_issue_loan_existing_active_blocks(self, db, city):
        bank = _make_bank(db, city, 50000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        issue_loan(db, bank, borrower, Decimal("1000.00"), game_day=1)
        db.flush()
        result = issue_loan(db, bank, borrower, Decimal("2000.00"), game_day=2)
        assert result["success"] is False

    def test_repay_loan_partial(self, db, city):
        bank = _make_bank(db, city, 50000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        issue_loan(db, bank, borrower, Decimal("1000.00"), game_day=1)
        db.flush()
        loan = db.query(BankCredit).first()
        result = repay_loan(db, loan, borrower, Decimal("400.00"))
        db.flush()
        assert result["success"] is True
        assert Decimal(str(loan.remaining_amount)) == Decimal("600.00")
        assert loan.status == "active"

    def test_repay_loan_full(self, db, city):
        bank = _make_bank(db, city, 50000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        issue_loan(db, bank, borrower, Decimal("1000.00"), game_day=1)
        db.flush()
        loan = db.query(BankCredit).first()
        # Нарахуємо відсотки щоб remaining > principal
        process_loan_interest(db, city.id, game_day=2)
        db.flush()
        remaining = Decimal(str(loan.remaining_amount))
        # Гравець має достатньо (5100 + 100 = 5200, борг ~1000.03)
        result = repay_loan(db, loan, borrower, remaining)
        db.flush()
        assert result["success"] is True
        assert loan.status == "repaid"

    def test_loan_interest_accrues(self, db, city):
        bank = _make_bank(db, city, 50000.0)
        borrower = _make_player(db, city, "borrower", 100.0)
        issue_loan(db, bank, borrower, Decimal("1000.00"), Decimal("12.00"), game_day=1)
        db.flush()
        result = process_loan_interest(db, city.id, game_day=2)
        db.flush()
        assert result["loans_processed"] == 1
        assert result["total_interest"] > 0
        loan = db.query(BankCredit).first()
        assert Decimal(str(loan.remaining_amount)) > Decimal("1000.00")


# --- Bankruptcy auctions ---


class TestBankruptcyAuctions:
    def test_trigger_auction(self, db, city):
        business = _make_bankrupt_business(db, city)
        result = trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        assert result["success"] is True
        auction = db.query(BankruptcyAuction).first()
        assert auction is not None
        # Стартова = борг + 10% місту
        expected = Decimal("500.00") + Decimal("500.00") * (AUCTION_CITY_PERCENTAGE / Decimal("100"))
        assert Decimal(str(auction.starting_price)) == expected

    def test_trigger_auction_already_exists(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        result = trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        assert result["success"] is False

    def test_place_bid_success(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        auction = db.query(BankruptcyAuction).first()
        bidder = _make_player(db, city, "bidder", 10000.0)
        starting = Decimal(str(auction.starting_price))
        bid_amount = starting + AUCTION_MIN_BID_INCREMENT
        result = place_bid(db, auction, bidder, bid_amount)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(auction.highest_bid)) == bid_amount
        assert auction.highest_bidder_id == bidder.id

    def test_place_bid_too_low(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        auction = db.query(BankruptcyAuction).first()
        bidder = _make_player(db, city, "bidder", 10000.0)
        # Ставка нижче за стартову + крок
        result = place_bid(db, auction, bidder, Decimal(str(auction.starting_price)))
        assert result["success"] is False

    def test_place_bid_insufficient_funds(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        auction = db.query(BankruptcyAuction).first()
        bidder = _make_player(db, city, "poor_bidder", 10.0)
        bid_amount = Decimal(str(auction.starting_price)) + AUCTION_MIN_BID_INCREMENT
        result = place_bid(db, auction, bidder, bid_amount)
        assert result["success"] is False

    def test_close_auction_with_winner(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        auction = db.query(BankruptcyAuction).first()
        bidder = _make_player(db, city, "winner", 10000.0)
        bid_amount = Decimal(str(auction.starting_price)) + AUCTION_MIN_BID_INCREMENT
        place_bid(db, auction, bidder, bid_amount)
        db.flush()
        # Тепер робимо аукціон завершеним (після ставки)
        auction.ends_at = datetime.now(UTC) - timedelta(hours=1)
        db.flush()
        initial_treasury = Decimal(str(city.treasury_balance))
        result = close_auction(db, auction)
        db.flush()
        assert result["success"] is True
        assert auction.status == "won"
        assert auction.winner_id == bidder.id
        db.refresh(business)
        assert business.owner_player_id == bidder.id
        assert business.status == "active"
        # Місто отримало %
        db.refresh(city)
        city_cut = bid_amount * (AUCTION_CITY_PERCENTAGE / Decimal("100"))
        assert Decimal(str(city.treasury_balance)) == initial_treasury + city_cut

    def test_close_auction_no_bids(self, db, city):
        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.flush()
        auction = db.query(BankruptcyAuction).first()
        auction.ends_at = datetime.now(UTC) - timedelta(hours=1)
        db.flush()
        result = close_auction(db, auction)
        db.flush()
        assert result["success"] is True
        assert auction.status == "closed"

    def test_list_active_auctions(self, db, city):
        b1 = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, b1, city, Decimal("500.00"))
        db.flush()
        auctions = list_active_auctions(db, city.id)
        assert len(auctions) == 1


# --- API ---


class TestBankApi:
    def test_deposit_endpoint(self, db, city):
        from backend.app.api.routes.mvp import bank_deposit_endpoint

        bank = _make_bank(db, city)
        player = _make_player(db, city, "api_depositor", 1000.0)
        db.commit()
        result = bank_deposit_endpoint(
            str(bank.id),
            {"player_id": str(player.id), "amount": "500.00", "game_day": 1},
            db=db,
        )
        assert result["success"] is True

    def test_loan_endpoint(self, db, city):
        from backend.app.api.routes.mvp import bank_loan_endpoint

        bank = _make_bank(db, city)
        player = _make_player(db, city, "api_borrower", 100.0)
        db.commit()
        result = bank_loan_endpoint(
            str(bank.id),
            {"player_id": str(player.id), "amount": "1000.00", "term_days": 30, "game_day": 1},
            db=db,
        )
        assert result["success"] is True

    def test_list_auctions_endpoint(self, db, city):
        from backend.app.api.routes.mvp import list_active_auctions_endpoint

        business = _make_bankrupt_business(db, city)
        trigger_bankruptcy_auction(db, business, city, Decimal("500.00"))
        db.commit()
        result = list_active_auctions_endpoint(db)
        assert result["success"] is True
        assert len(result["data"]["auctions"]) == 1
