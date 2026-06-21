"""
Адвокатська система (Phase G8).

Механіки:
- Супровід угод: success_chance_bonus, detection_chance_reduction.
- Апеляція: адвокат супроводжує в суді.
- Захист від поліції.
- successful_deals росте → нижчий шанс перевірки.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import CourtCase, LawyerEngagement, Player

logger = logging.getLogger("LawyerService")

# --- Константи ---
LAWYER_COMMISSION_PCT = 0.10  # 10% від суми угоди
SUCCESS_CHANCE_BONUS_PER_LEVEL = 0.05  # +5% за кожен рівень досвіду
DETECTION_REDUCTION_PER_LEVEL = 0.03  # -3% шанс перевірки
LEVEL_UP_DEALS = 10  # стільки успішних угод для рівня


def engage_lawyer(
    db: Session,
    lawyer: Player,
    client: Player,
    deal_type: str,
    amount: Decimal,
    game_day: int = 0,
) -> dict:
    """Клієнт наймає адвоката для супроводу угоди."""
    if lawyer.id == client.id:
        return {"success": False, "message": "Не можна найняти себе."}

    # Розрахунок комісії
    commission = amount * Decimal(str(LAWYER_COMMISSION_PCT))

    # Бонус шансу успіху залежить від досвіду адвоката
    lawyer_level = get_lawyer_level(db, lawyer.id)
    success_bonus = lawyer_level * SUCCESS_CHANCE_BONUS_PER_LEVEL
    detection_reduction = lawyer_level * DETECTION_REDUCTION_PER_LEVEL

    engagement = LawyerEngagement(
        lawyer_id=lawyer.id,
        client_id=client.id,
        deal_type=deal_type,
        amount=float(amount),
        commission=float(commission),
        success_chance_bonus=success_bonus,
    )
    db.add(engagement)
    db.flush()

    # Клієнт платить комісію
    if Decimal(str(client.balance)) >= commission:
        client.balance = Decimal(str(client.balance)) - commission
        lawyer.balance = Decimal(str(lawyer.balance)) + commission

    db.flush()
    logger.info("Адвокат %s найнятий клієнтом %s для %s", lawyer.username, client.username, deal_type)
    return {
        "success": True,
        "message": "Адвокат найнятий.",
        "engagement_id": str(engagement.id),
        "commission": float(commission),
        "success_chance_bonus": success_bonus,
        "detection_chance_reduction": detection_reduction,
    }


def get_lawyer_level(db: Session, lawyer_id: uuid.UUID) -> int:
    """Повертає рівень адвоката за кількістю успішних угод."""
    successful = (
        db.query(LawyerEngagement)
        .filter(
            LawyerEngagement.lawyer_id == lawyer_id,
            LawyerEngagement.is_successful.is_(True),
        )
        .count()
    )
    return successful // LEVEL_UP_DEALS


def complete_engagement(
    db: Session,
    engagement: LawyerEngagement,
    is_successful: bool,
) -> dict:
    """Завершення угоди — позначаємо результат."""
    engagement.is_successful = is_successful
    db.flush()

    if is_successful:
        level = get_lawyer_level(db, engagement.lawyer_id)
        return {
            "success": True,
            "message": f"Угода успішна. Рівень адвоката: {level}.",
            "lawyer_level": level,
        }
    return {"success": True, "message": "Угода провалена."}


def appeal_with_lawyer(
    db: Session,
    case: CourtCase,
    lawyer: Player,
    client: Player,
    game_day: int = 0,
) -> dict:
    """Адвокат допомагає з апеляцією — підвищує шанс успіху."""
    from backend.app.services.court_service import file_appeal

    result = file_appeal(db, case, client, game_day)
    if not result["success"]:
        return result

    # Бонус адвоката: знижує resistance суддів
    lawyer_level = get_lawyer_level(db, lawyer.id)
    bonus = lawyer_level * 0.05  # -5% до resistance за рівень

    db.flush()
    return {
        "success": True,
        "message": f"Апеляція подана з адвокатом (рівень {lawyer_level}). Бонус: -{bonus * 100}% resistance суддів.",
        "lawyer_level": lawyer_level,
        "resistance_reduction": bonus,
    }


def defend_against_police(
    db: Session,
    lawyer: Player,
    client: Player,
    game_day: int = 0,
) -> dict:
    """Адвокат захищає клієнта від поліції — знижує шанс арешту."""
    lawyer_level = get_lawyer_level(db, lawyer.id)
    defense_bonus = lawyer_level * 0.08  # -8% шанс арешту за рівень

    engagement = LawyerEngagement(
        lawyer_id=lawyer.id,
        client_id=client.id,
        deal_type="police_defense",
        amount=0.0,
        commission=0.0,
        success_chance_bonus=defense_bonus,
    )
    db.add(engagement)
    db.flush()
    return {
        "success": True,
        "message": f"Адвокат захищає. Шанс арешту -{defense_bonus * 100}%.",
        "defense_bonus": defense_bonus,
    }
