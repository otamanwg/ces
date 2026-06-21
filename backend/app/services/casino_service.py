"""
Казино як бізнес (Phase G9).

Механіки:
- Casino blueprint (оперує з власного cash_balance бізнесу).
- Blackjack: гравець проти дилера, виграш 2x ставки, казино платить з cash_balance, rake залишається казино.
- Roulette: ставки на red/black/even/odd/number, виплата 2x або 36x.
- Poker: створення гри (waiting) → завершення (settle) з rake та податком у казначейство міста.
- Податок на доход казино (25% щоденного прибутку) → treasury.
- Щомісячна ліцензійна плата → treasury.
- Відкликання ліцензії мером (shut_down).
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, CasinoGame, City, Player

logger = logging.getLogger("CasinoService")

# --- Ставки та податки ---
RAKE_PCT = Decimal("0.07")  # 7% від банку (pot)
BLACKJACK_WIN_CHANCE = 0.49  # ймовірність виграшу гравця у blackjack
ROULETTE_WIN_CHANCE = 0.473  # ймовірність для red/black/even/odd (~18/38)
CASINO_TAX_PCT = Decimal("0.25")  # 25% податок на доход казино → treasury
LICENSE_FEE_MONTHLY = Decimal("500.00")  # щомісячна ліцензійна плата

# --- Blackjack ---


def play_blackjack(db: Session, casino_business: Business, player: Player, bet: Decimal) -> dict:
    """Гравець грає в blackjack проти дилера казино.

    Виграш = 2x ставки. Казино виплачує з cash_balance, rake (7%) залишається казино.
    """
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    if casino_business.status != "active":
        return {"success": False, "message": "Казино закрито або неактивне."}

    bet = Decimal(str(bet))
    if bet <= 0:
        return {"success": False, "message": "Ставка має бути додатною."}

    if Decimal(str(player.balance)) < bet:
        return {"success": False, "message": "Недостатньо коштів для ставки."}

    # Гравець робить ставку → гроші переходять у касу казино
    player.balance = Decimal(str(player.balance)) - bet
    casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) + bet

    won = random.random() < BLACKJACK_WIN_CHANCE

    if won:
        pot = bet * Decimal("2")
        rake = (pot * RAKE_PCT).quantize(Decimal("0.01"))
        payout = pot - rake
        # Казино виплачує виграш гравцю з cash_balance (rake залишається казино)
        player.balance = Decimal(str(player.balance)) + payout
        casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) - payout
        db.flush()
        logger.info(
            "Blackjack виграш: гравець=%s, ставка=%s, виплата=%s, rake=%s",
            player.username,
            bet,
            payout,
            rake,
        )
        return {
            "success": True,
            "message": "Ви виграли в blackjack!",
            "won": True,
            "winnings": float(payout),
            "rake": float(rake),
        }

    db.flush()
    logger.info("Blackjack програш: гравець=%s, ставка=%s", player.username, bet)
    return {
        "success": True,
        "message": "Дилер виграв. Ви втратили ставку.",
        "won": False,
        "loss": float(bet),
    }


# --- Roulette ---


def play_roulette(
    db: Session,
    casino_business: Business,
    player: Player,
    bet: Decimal,
    bet_type: str,
) -> dict:
    """Гравець грає в рулетку.

    bet_type: "red", "black", "even", "odd", "number".
    Виплата 2x для red/black/even/odd, 36x для number.
    """
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    if casino_business.status != "active":
        return {"success": False, "message": "Казино закрито або неактивне."}

    valid_types = ("red", "black", "even", "odd", "number")
    if bet_type not in valid_types:
        return {
            "success": False,
            "message": f"Невірний тип ставки. Доступні: {', '.join(valid_types)}.",
        }

    bet = Decimal(str(bet))
    if bet <= 0:
        return {"success": False, "message": "Ставка має бути додатною."}

    if Decimal(str(player.balance)) < bet:
        return {"success": False, "message": "Недостатньо коштів для ставки."}

    # Ймовірність виграшу залежить від типу ставки
    if bet_type == "number":
        win_chance = Decimal("1") / Decimal("37")  # ~0.027 для європейської рулетки
        payout_mult = Decimal("36")
    else:
        win_chance = Decimal(str(ROULETTE_WIN_CHANCE))
        payout_mult = Decimal("2")

    # Гравець робить ставку → гроші переходять у касу казино
    player.balance = Decimal(str(player.balance)) - bet
    casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) + bet

    won = random.random() < float(win_chance)

    if won:
        pot = bet * payout_mult
        rake = (pot * RAKE_PCT).quantize(Decimal("0.01"))
        payout = pot - rake
        player.balance = Decimal(str(player.balance)) + payout
        casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) - payout
        db.flush()
        logger.info(
            "Roulette виграш: гравець=%s, тип=%s, ставка=%s, виплата=%s, rake=%s",
            player.username,
            bet_type,
            bet,
            payout,
            rake,
        )
        return {
            "success": True,
            "message": f"Ви виграли в рулетку (ставка: {bet_type})!",
            "won": True,
            "winnings": float(payout),
            "rake": float(rake),
        }

    db.flush()
    logger.info("Roulette програш: гравець=%s, тип=%s, ставка=%s", player.username, bet_type, bet)
    return {
        "success": True,
        "message": f"Невдача у рулетці (ставка: {bet_type}). Ви втратили ставку.",
        "won": False,
        "loss": float(bet),
    }


# --- Poker ---


def create_poker_game(db: Session, casino_business: Business, min_buyin: Decimal) -> dict:
    """Створює покерну гру зі статусом 'waiting'."""
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    if casino_business.status != "active":
        return {"success": False, "message": "Казино закрито або неактивне."}

    min_buyin = Decimal(str(min_buyin))
    if min_buyin <= 0:
        return {"success": False, "message": "Мінімальний buy-in має бути додатнім."}

    game = CasinoGame(
        casino_business_id=casino_business.id,
        game_type="poker",
        status="waiting",
        players=[],
        pot=Decimal("0.00"),
        rake=Decimal("0.00"),
    )
    db.add(game)
    db.flush()
    logger.info(
        "Покерну гру створено: казино=%s, min_buyin=%s, game_id=%s",
        casino_business.id,
        min_buyin,
        game.id,
    )
    return {
        "success": True,
        "message": "Покерну гру створено. Очікування гравців.",
        "game_id": str(game.id),
        "min_buyin": float(min_buyin),
    }


def settle_poker_game(db: Session, game: CasinoGame, winner: Player, pot: Decimal) -> dict:
    """Завершує покерну гру: переможець отримує pot мінус rake, rake — казино, податок — у treasury."""
    if game.status != "waiting" and game.status != "in_progress":
        return {"success": False, "message": "Гру вже завершено."}

    pot = Decimal(str(pot))
    if pot <= 0:
        return {"success": False, "message": "Банк (pot) має бути додатнім."}

    rake = (pot * RAKE_PCT).quantize(Decimal("0.01"))
    winner_payout = pot - rake

    # Переможець отримує pot мінус rake
    winner.balance = Decimal(str(winner.balance)) + winner_payout

    # Rake залишається казино
    casino = db.query(Business).filter(Business.id == game.casino_business_id).first()
    if not casino:
        return {"success": False, "message": "Казино-бізнес не знайдено."}

    casino.cash_balance = Decimal(str(casino.cash_balance)) + rake

    # Податок на доход казино (25% від rake) → treasury міста
    tax = (rake * CASINO_TAX_PCT).quantize(Decimal("0.01"))
    casino.cash_balance = Decimal(str(casino.cash_balance)) - tax

    city = db.query(City).filter(City.id == casino.city_id).first()
    if city:
        city.treasury_balance = Decimal(str(city.treasury_balance)) + tax
    else:
        logger.warning("Місто для казино %s не знайдено — податок %s не перераховано.", casino.id, tax)

    # Завершуємо гру
    game.status = "finished"
    game.winner_id = winner.id
    game.pot = pot
    game.rake = rake
    game.finished_at = datetime.now(UTC)

    db.flush()
    logger.info(
        "Покерну гру завершено: game_id=%s, переможець=%s, pot=%s, rake=%s, payout=%s, tax=%s",
        game.id,
        winner.username,
        pot,
        rake,
        winner_payout,
        tax,
    )
    return {
        "success": True,
        "message": "Покерну гри завершено. Переможцю виплачено банк.",
        "winner": winner.username,
        "pot": float(pot),
        "rake": float(rake),
        "winnings": float(winner_payout),
        "tax": float(tax),
    }


# --- Податки та ліцензія ---


def collect_casino_tax(db: Session, casino_business: Business, city: City) -> dict:
    """25% щоденного прибутку казино → treasury міста."""
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    daily_profit = Decimal(str(casino_business.daily_revenue))
    if daily_profit <= 0:
        return {"success": True, "message": "Прибуток за день відсутній — податок не нараховано.", "tax": 0.0}

    tax = (daily_profit * CASINO_TAX_PCT).quantize(Decimal("0.01"))

    if Decimal(str(casino_business.cash_balance)) < tax:
        return {"success": False, "message": "Недостатньо коштів у казино для сплати податку."}

    casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) - tax
    city.treasury_balance = Decimal(str(city.treasury_balance)) + tax
    db.flush()
    logger.info(
        "Податок на доход казино зібрано: казино=%s, прибуток=%s, податок=%s",
        casino_business.id,
        daily_profit,
        tax,
    )
    return {
        "success": True,
        "message": "Податок на доход казино перераховано до казначейства.",
        "tax": float(tax),
        "daily_profit": float(daily_profit),
    }


def pay_license_fee(db: Session, casino_business: Business, city: City) -> dict:
    """Щомісячна ліцензійна плата з cash_balance казино → treasury міста."""
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    if Decimal(str(casino_business.cash_balance)) < LICENSE_FEE_MONTHLY:
        return {"success": False, "message": "Недостатньо коштів для сплати ліцензійної плати."}

    casino_business.cash_balance = Decimal(str(casino_business.cash_balance)) - LICENSE_FEE_MONTHLY
    city.treasury_balance = Decimal(str(city.treasury_balance)) + LICENSE_FEE_MONTHLY
    db.flush()
    logger.info("Ліцензійна плата сплачена: казино=%s, сума=%s", casino_business.id, LICENSE_FEE_MONTHLY)
    return {
        "success": True,
        "message": "Ліцензійна плата сплачена.",
        "fee": float(LICENSE_FEE_MONTHLY),
    }


# --- Відкликання ліцензії ---


def shut_down_casino(db: Session, casino_business: Business, reason: str) -> dict:
    """Мір відкликає ліцензію: казино переводиться у неактивний статус."""
    if casino_business.type != "casino":
        return {"success": False, "message": "Цей бізнес не є казино."}

    if casino_business.status != "active":
        return {"success": False, "message": "Казино вже неактивне."}

    casino_business.status = "closed"
    db.flush()
    logger.info("Казино закрито мером: казино=%s, причина=%s", casino_business.id, reason)
    return {
        "success": True,
        "message": f"Ліцензію казино відкликано. Причина: {reason}",
        "reason": reason,
    }
