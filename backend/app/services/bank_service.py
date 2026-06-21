"""
Банк як бізнес (Phase G5).

Механіки:
- Bank blueprint (окремий, оперує з власного cash_balance).
- Депозити: гравець кладе гроші, отримує щоденний відсоток.
- Кредити: банк видає з власного балансу, гравець повертає з відсотком.
- AI-банк: умови з економіки (базові ставки).
- Банк гравця: гравець обирає ставки (через API).
- Банкрутство бізнесу → аукціон (24 години реального часу).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import (
    BankCredit,
    BankDeposit,
    BankruptcyAuction,
    Business,
    City,
    Player,
)

logger = logging.getLogger("BankService")

# --- Базові ставки (AI-банк) ---
DEFAULT_DEPOSIT_RATE = Decimal("5.00")  # 5% річних → щоденний ~0.014%
DEFAULT_LOAN_RATE = Decimal("12.00")  # 12% річних
DEFAULT_LOAN_TERM_DAYS = 30
MAX_LOAN_AMOUNT = Decimal("50000.00")
MIN_LOAN_AMOUNT = Decimal("100.00")
MAX_DEPOSIT_RATE = Decimal("20.00")
MAX_LOAN_RATE = Decimal("30.00")

# Аукціон банкрутів
AUCTION_DURATION_HOURS = 24
AUCTION_CITY_PERCENTAGE = Decimal("10.00")  # місто бере 10% з ціни продажу
AUCTION_MIN_BID_INCREMENT = Decimal("100.00")  # мінімальний крок ставки


def _daily_rate(annual_rate: Decimal) -> Decimal:
    """Конвертує річну ставку у щоденну (простий поділ на 365)."""
    return annual_rate / Decimal("365")


# --- Депозити ---


def create_deposit(
    db: Session,
    bank: Business,
    player: Player,
    amount: Decimal,
    interest_rate: Decimal | None = None,
    game_day: int = 0,
) -> dict:
    """Гравець кладе депозит у банк.

    Гроші переходять з balance гравця у cash_balance банку.
    """
    if bank.type != "bank":
        return {"success": False, "message": "Цей бізнес не є банком."}

    if amount <= 0:
        return {"success": False, "message": "Сума депозиту має бути додатною."}

    if Decimal(str(player.balance)) < amount:
        return {"success": False, "message": "Недостатньо коштів для депозиту."}

    rate = interest_rate if interest_rate is not None else DEFAULT_DEPOSIT_RATE
    if rate < 0 or rate > MAX_DEPOSIT_RATE:
        return {"success": False, "message": f"Ставка має бути від 0 до {MAX_DEPOSIT_RATE}%."}

    player.balance = Decimal(str(player.balance)) - amount
    bank.cash_balance = Decimal(str(bank.cash_balance)) + amount

    deposit = BankDeposit(
        bank_business_id=bank.id,
        player_id=player.id,
        amount=amount,
        interest_rate=rate,
        created_at_game_day=game_day,
        last_interest_game_day=game_day,
        is_active=True,
    )
    db.add(deposit)
    db.flush()
    logger.info("Депозит %s створено: гравець=%s, ставка=%s%%", amount, player.username, rate)
    return {
        "success": True,
        "message": "Депозит успішно створено.",
        "deposit": {
            "id": str(deposit.id),
            "amount": float(amount),
            "interest_rate": float(rate),
            "game_day": game_day,
        },
    }


def withdraw_deposit(db: Session, deposit: BankDeposit, player: Player) -> dict:
    """Гравець знімає депозит (повна сума + нараховані відсотки)."""
    if deposit.player_id != player.id:
        return {"success": False, "message": "Це не ваш депозит."}

    if not deposit.is_active:
        return {"success": False, "message": "Депозит вже закритий."}

    bank = db.query(Business).filter(Business.id == deposit.bank_business_id).first()
    if not bank:
        return {"success": False, "message": "Банк не знайдено."}

    total = Decimal(str(deposit.amount))
    if Decimal(str(bank.cash_balance)) < total:
        return {"success": False, "message": "Банк не має достатньо коштів для виплати."}

    bank.cash_balance = Decimal(str(bank.cash_balance)) - total
    player.balance = Decimal(str(player.balance)) + total
    deposit.is_active = False
    db.flush()
    logger.info("Депозит %s знято: гравець=%s, сума=%s", deposit.id, player.username, total)
    return {"success": True, "message": "Депозит знято.", "amount": float(total)}


def process_deposit_interest(db: Session, city_id: uuid.UUID, game_day: int) -> dict:
    """Щоденне нарахування відсотків по всіх активних депозитах міста."""
    deposits = (
        db.query(BankDeposit)
        .join(Business)
        .filter(
            Business.city_id == city_id,
            BankDeposit.is_active.is_(True),
            BankDeposit.last_interest_game_day < game_day,
        )
        .all()
    )
    total_interest = Decimal("0.00")
    for deposit in deposits:
        days_elapsed = game_day - deposit.last_interest_game_day
        if days_elapsed <= 0:
            continue
        daily = _daily_rate(Decimal(str(deposit.interest_rate)))
        interest = Decimal(str(deposit.amount)) * daily * Decimal(str(days_elapsed))
        deposit.amount = Decimal(str(deposit.amount)) + interest
        deposit.last_interest_game_day = game_day
        total_interest += interest
    db.flush()
    return {"deposits_processed": len(deposits), "total_interest": float(total_interest)}


# --- Кредити ---


def issue_loan(
    db: Session,
    bank: Business,
    borrower: Player,
    amount: Decimal,
    interest_rate: Decimal | None = None,
    term_days: int = DEFAULT_LOAN_TERM_DAYS,
    game_day: int = 0,
) -> dict:
    """Банк видає кредит гравцю.

    Гроші переходять з cash_balance банку у balance гравця.
    Гравець зобов'язаний повернути principal + interest до due_game_day.
    """
    if bank.type != "bank":
        return {"success": False, "message": "Цей бізнес не є банком."}

    if amount < MIN_LOAN_AMOUNT or amount > MAX_LOAN_AMOUNT:
        return {
            "success": False,
            "message": f"Сума кредиту має бути від {MIN_LOAN_AMOUNT} до {MAX_LOAN_AMOUNT}.",
        }

    if Decimal(str(bank.cash_balance)) < amount:
        return {"success": False, "message": "Банк не має достатньо коштів для кредиту."}

    # Перевірка наявних активних кредитів (один активний за раз)
    existing = (
        db.query(BankCredit)
        .filter(
            BankCredit.borrower_player_id == borrower.id,
            BankCredit.status == "active",
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "У вас вже є активний кредит. Спочатку погасіть."}

    rate = interest_rate if interest_rate is not None else DEFAULT_LOAN_RATE
    if rate < 0 or rate > MAX_LOAN_RATE:
        return {"success": False, "message": f"Ставка має бути від 0 до {MAX_LOAN_RATE}%."}

    bank.cash_balance = Decimal(str(bank.cash_balance)) - amount
    borrower.balance = Decimal(str(borrower.balance)) + amount

    loan = BankCredit(
        bank_business_id=bank.id,
        borrower_player_id=borrower.id,
        principal_amount=amount,
        remaining_amount=amount,
        interest_rate=rate,
        term_days=term_days,
        created_at_game_day=game_day,
        due_game_day=game_day + term_days,
        status="active",
    )
    db.add(loan)
    db.flush()
    logger.info(
        "Кредит %s видано: позичальник=%s, ставка=%s%%, термін=%d днів", amount, borrower.username, rate, term_days
    )
    return {
        "success": True,
        "message": "Кредит успішно видано.",
        "loan": {
            "id": str(loan.id),
            "amount": float(amount),
            "interest_rate": float(rate),
            "term_days": term_days,
            "due_game_day": loan.due_game_day,
        },
    }


def repay_loan(db: Session, loan: BankCredit, borrower: Player, amount: Decimal) -> dict:
    """Гравець погашає кредит (частково або повністю)."""
    if loan.borrower_player_id != borrower.id:
        return {"success": False, "message": "Це не ваш кредит."}

    if loan.status != "active":
        return {"success": False, "message": "Кредит не активний."}

    if amount <= 0:
        return {"success": False, "message": "Сума погашення має бути додатною."}

    remaining = Decimal(str(loan.remaining_amount))
    pay_amount = min(amount, remaining)

    if Decimal(str(borrower.balance)) < pay_amount:
        return {"success": False, "message": "Недостатньо коштів для погашення."}

    bank = db.query(Business).filter(Business.id == loan.bank_business_id).first()
    if not bank:
        return {"success": False, "message": "Банк не знайдено."}

    borrower.balance = Decimal(str(borrower.balance)) - pay_amount
    bank.cash_balance = Decimal(str(bank.cash_balance)) + pay_amount
    loan.remaining_amount = remaining - pay_amount

    if Decimal(str(loan.remaining_amount)) <= 0:
        loan.status = "repaid"
        logger.info("Кредит %s повністю погашено", loan.id)
    db.flush()
    return {
        "success": True,
        "message": "Платіж прийнято.",
        "paid": float(pay_amount),
        "remaining": float(loan.remaining_amount),
    }


def process_loan_interest(db: Session, city_id: uuid.UUID, game_day: int) -> dict:
    """Щоденне нарахування відсотків по активних кредитах + перевірка дефолтів."""
    loans = (
        db.query(BankCredit)
        .join(Business)
        .filter(
            Business.city_id == city_id,
            BankCredit.status == "active",
        )
        .all()
    )
    total_interest = Decimal("0.00")
    defaults = 0
    for loan in loans:
        daily = _daily_rate(Decimal(str(loan.interest_rate)))
        interest = Decimal(str(loan.remaining_amount)) * daily
        loan.remaining_amount = Decimal(str(loan.remaining_amount)) + interest
        total_interest += interest

        # Перевірка дефолту: прострочення
        if game_day > loan.due_game_day:
            borrower = db.query(Player).filter(Player.id == loan.borrower_player_id).first()
            if borrower and Decimal(str(borrower.balance)) < Decimal(str(loan.remaining_amount)):
                loan.status = "defaulted"
                defaults += 1
                logger.warning("Кредит %s у дефолті: позичальник=%s", loan.id, borrower.username)
    db.flush()
    return {
        "loans_processed": len(loans),
        "total_interest": float(total_interest),
        "defaults": defaults,
    }


# --- Аукціон банкрутів ---


def trigger_bankruptcy_auction(
    db: Session,
    business: Business,
    city: City,
    debt_amount: Decimal | None = None,
) -> dict:
    """Створює аукціон банкрутів для бізнесу.

    Стартова ціна = борги + % місту. Термін — 24 години реального часу.
    """
    if business.status != "bankrupt":
        return {"success": False, "message": "Бізнес не банкрот."}

    # Перевіряємо що немає активного аукціону
    existing = (
        db.query(BankruptcyAuction)
        .filter(
            BankruptcyAuction.business_id == business.id,
            BankruptcyAuction.status == "active",
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Аукціон вже існує для цього бізнесу."}

    debt = debt_amount if debt_amount is not None else Decimal("0.00")
    city_cut = debt * (AUCTION_CITY_PERCENTAGE / Decimal("100"))
    starting_price = debt + city_cut

    if starting_price <= 0:
        starting_price = Decimal("100.00")  # мінімальна ціна

    now = datetime.now(UTC)
    auction = BankruptcyAuction(
        business_id=business.id,
        city_id=city.id,
        starting_price=starting_price,
        debt_amount=debt,
        city_percentage=AUCTION_CITY_PERCENTAGE,
        highest_bid=starting_price,
        highest_bidder_id=None,
        started_at=now,
        ends_at=now + timedelta(hours=AUCTION_DURATION_HOURS),
        status="active",
    )
    db.add(auction)
    db.flush()
    logger.info(
        "Аукціон банкрутів створено: бізнес=%s, стартова ціна=%s, до=%s",
        business.name,
        starting_price,
        auction.ends_at,
    )
    return {
        "success": True,
        "message": "Аукціон банкрутів створено.",
        "auction": {
            "id": str(auction.id),
            "business_id": str(business.id),
            "starting_price": float(starting_price),
            "ends_at": auction.ends_at.isoformat(),
        },
    }


def place_bid(
    db: Session,
    auction: BankruptcyAuction,
    bidder: Player,
    amount: Decimal,
) -> dict:
    """Гравець робить ставку на аукціоні банкрутів."""
    if auction.status != "active":
        return {"success": False, "message": "Аукціон не активний."}

    now = datetime.now(UTC)
    if now > auction.ends_at:
        return {"success": False, "message": "Аукціон завершено."}

    current_bid = Decimal(str(auction.highest_bid))
    min_bid = current_bid + AUCTION_MIN_BID_INCREMENT
    if amount < min_bid:
        return {
            "success": False,
            "message": f"Ставка має бути не менше {min_bid} (поточна + крок).",
        }

    if Decimal(str(bidder.balance)) < amount:
        return {"success": False, "message": "Недостатньо коштів для ставки."}

    # AI-мер не купує (перевірка — якщо bidder.is_ai_mayor, відхиляємо)
    # Phase G6: додамо поле is_ai_mayor на Player. Поки дозволяємо всім.

    from backend.app.models import AuctionBid

    bid = AuctionBid(
        auction_id=auction.id,
        bidder_id=bidder.id,
        amount=amount,
    )
    db.add(bid)
    auction.highest_bid = amount
    auction.highest_bidder_id = bidder.id
    db.flush()
    logger.info("Ставка на аукціоні: гравець=%s, сума=%s", bidder.username, amount)
    return {
        "success": True,
        "message": "Ставку прийнято.",
        "bid": float(amount),
        "is_highest": True,
    }


def close_auction(db: Session, auction: BankruptcyAuction) -> dict:
    """Закриває аукціон: визначає переможця, передає бізнес."""
    if auction.status != "active":
        return {"success": False, "message": "Аукціон вже закритий."}

    now = datetime.now(UTC)
    if now < auction.ends_at:
        return {"success": False, "message": "Аукціон ще не завершився."}

    if auction.highest_bidder_id is None:
        auction.status = "closed"
        db.flush()
        return {"success": True, "message": "Аукціон закрито без переможця."}

    winner = db.query(Player).filter(Player.id == auction.highest_bidder_id).first()
    if not winner or Decimal(str(winner.balance)) < Decimal(str(auction.highest_bid)):
        auction.status = "closed"
        db.flush()
        return {"success": True, "message": "Переможець не має коштів. Аукціон закрито."}

    business = db.query(Business).filter(Business.id == auction.business_id).first()
    if not business:
        auction.status = "closed"
        db.flush()
        return {"success": False, "message": "Бізнес не знайдено."}

    # Оплата
    winning_bid = Decimal(str(auction.highest_bid))
    city_cut = winning_bid * (Decimal(str(auction.city_percentage)) / Decimal("100"))
    winner.balance = Decimal(str(winner.balance)) - winning_bid

    city = db.query(City).filter(City.id == auction.city_id).first()
    if city:
        city.treasury_balance = Decimal(str(city.treasury_balance)) + city_cut

    # Передача бізнесу
    business.owner_player_id = winner.id
    business.status = "active"
    business.cash_balance = winning_bid - city_cut  # залишок новому власнику

    auction.status = "won"
    auction.winner_id = winner.id
    auction.winning_bid = winning_bid
    db.flush()
    logger.info(
        "Аукціон виграно: переможець=%s, ціна=%s, місту=%s",
        winner.username,
        winning_bid,
        city_cut,
    )
    return {
        "success": True,
        "message": "Бізнес передано переможцю.",
        "winner": winner.username,
        "winning_bid": float(winning_bid),
        "city_cut": float(city_cut),
    }


def list_active_auctions(db: Session, city_id: uuid.UUID | None = None) -> list[BankruptcyAuction]:
    """Повертає активні аукціони банкрутів."""
    query = db.query(BankruptcyAuction).filter(BankruptcyAuction.status == "active")
    if city_id is not None:
        query = query.filter(BankruptcyAuction.city_id == city_id)
    return query.order_by(BankruptcyAuction.ends_at.asc()).all()
