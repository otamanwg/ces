"""
Тюремна система (Phase G8).

Механіки:
- Ув'язнення: days_served росте на day tick.
- Покер у тюрмі: вищі ставки, NPC-в'язні сильніші.
- Тюремна робота: низька зарплата, знижує термін.
- Соціалізація: кримінальні зв'язки.
- Good behavior: знижка 20-30%.
- Заморозка/конфіскація бізнесу.
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, Player, PrisonSentence

logger = logging.getLogger("PrisonService")

# --- Константи ---
PRISON_WORK_DAILY_PAY = Decimal("20.00")
PRISON_WORK_REDUCTION_DAYS = 1  # 1 день знижки за 3 дні роботи
GOOD_BEHAVIOR_REDUCTION_PCT = 0.25  # 25% знижка
POKER_MIN_BET = Decimal("50.00")
POKER_MAX_BET = Decimal("500.00")
POKER_WIN_CHANCE = 0.35  # нижче ніж звичайне казино


def get_active_sentence(db: Session, player_id: uuid.UUID) -> PrisonSentence | None:
    """Повертає активне ув'язнення гравця."""
    return (
        db.query(PrisonSentence)
        .filter(
            PrisonSentence.player_id == player_id,
            PrisonSentence.status == "serving",
        )
        .first()
    )


def serve_day(db: Session, sentence: PrisonSentence, game_day: int) -> dict:
    """Обробка одного дня ув'язнення на day tick."""
    sentence.days_served += 1
    sentence.days_remaining = max(0, sentence.days_remaining - 1)

    # Good behavior reduction
    if sentence.days_served >= sentence.days_total // 2:
        reduction = int(sentence.days_total * GOOD_BEHAVIOR_REDUCTION_PCT)
        if sentence.good_behavior_reduction < reduction:
            sentence.good_behavior_reduction = reduction
            sentence.days_remaining = max(0, sentence.days_remaining - 1)

    if sentence.days_remaining <= 0:
        sentence.status = "released"
        sentence.released_at = datetime.now(UTC)
        # Розморозка бізнесу якщо заморожений
        if sentence.frozen_business_id:
            business = db.query(Business).filter(Business.id == sentence.frozen_business_id).first()
            if business:
                business.is_active = True
        db.flush()
        logger.info("Гравець звільнений з тюрми (відсидів %d днів)", sentence.days_served)
        return {"success": True, "message": "Звільнення! Термін відсиджено.", "released": True}

    db.flush()
    return {
        "success": True,
        "message": f"День відсиджено. Залишилось {sentence.days_remaining} днів.",
        "days_remaining": sentence.days_remaining,
    }


def prison_work(db: Session, sentence: PrisonSentence, player: Player) -> dict:
    """Тюремна робота — заробіток + знижка терміну."""
    if sentence.status != "serving":
        return {"success": False, "message": "Ви не у тюрмі."}

    pay = PRISON_WORK_DAILY_PAY
    player.balance = Decimal(str(player.balance)) + pay

    # Кожні 3 дні роботи — 1 день знижки
    if sentence.days_served % 3 == 0:
        sentence.days_remaining = max(0, sentence.days_remaining - PRISON_WORK_REDUCTION_DAYS)
        sentence.good_behavior_reduction += PRISON_WORK_REDUCTION_DAYS

    db.flush()
    return {
        "success": True,
        "message": f"Праця в тюрмі. Зароблено {pay}.",
        "pay": float(pay),
        "days_remaining": sentence.days_remaining,
    }


def prison_poker(
    db: Session,
    sentence: PrisonSentence,
    player: Player,
    bet: Decimal,
) -> dict:
    """Покер у тюрмі — вищі ставки, нижчий шанс виграшу."""
    if sentence.status != "serving":
        return {"success": False, "message": "Ви не у тюрмі."}

    if bet < POKER_MIN_BET:
        return {"success": False, "message": f"Мінімальна ставка {POKER_MIN_BET}."}
    if bet > POKER_MAX_BET:
        return {"success": False, "message": f"Максимальна ставка {POKER_MAX_BET}."}

    if Decimal(str(player.balance)) < bet:
        return {"success": False, "message": "Недостатньо коштів."}

    player.balance = Decimal(str(player.balance)) - bet

    if random.random() < POKER_WIN_CHANCE:
        # Виграш 2x ставку
        winnings = bet * 2
        player.balance = Decimal(str(player.balance)) + winnings
        db.flush()
        return {
            "success": True,
            "message": f"Виграш! +{winnings}.",
            "won": True,
            "winnings": float(winnings),
        }
    else:
        db.flush()
        return {
            "success": True,
            "message": f"Програш. -{bet}.",
            "won": False,
            "loss": float(bet),
        }


def socialize(db: Session, sentence: PrisonSentence, player: Player) -> dict:
    """Соціалізація з NPC-в'язнями — кримінальні зв'язки."""
    if sentence.status != "serving":
        return {"success": False, "message": "Ви не у тюрмі."}

    # Спрощено: дає інформацію про тіньові схеми
    connections = random.randint(1, 3)
    # Можна зберігати в player metadata (спрощено)
    logger.info("Соціалізація: +%d кримінальних зв'язків", connections)
    return {
        "success": True,
        "message": f"Соціалізація: +{connections} кримінальних зв'язків.",
        "connections": connections,
    }


def freeze_business(db: Session, sentence: PrisonSentence, business: Business) -> dict:
    """Заморозка бізнесу під час ув'язнення."""
    if sentence.status != "serving":
        return {"success": False, "message": "Ви не у тюрмі."}

    business.is_active = False
    sentence.business_impact = "frozen"
    sentence.frozen_business_id = business.id
    db.flush()
    logger.info("Бізнес %s заморожено", business.name)
    return {"success": True, "message": f"Бізнес {business.name} заморожено."}


def unfreeze_business(db: Session, sentence: PrisonSentence) -> dict:
    """Розморозка бізнесу після звільнення."""
    if sentence.status != "released":
        return {"success": False, "message": "Спочатку відсидьте термін."}

    if not sentence.frozen_business_id:
        return {"success": False, "message": "Немає замороженого бізнесу."}

    business = db.query(Business).filter(Business.id == sentence.frozen_business_id).first()
    if business:
        business.is_active = True
        sentence.business_impact = "none"
        db.flush()
        return {"success": True, "message": f"Бізнес {business.name} розморожено."}
    return {"success": False, "message": "Бізнес не знайдено."}
