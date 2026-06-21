"""
Преса як бізнес (Phase G8).

Механіки:
- Media outlet blueprint (категорія media).
- Розслідування: накопичення press_evidence.
- Публікація: впливає на happiness, репутацію, evidence_strength.
- Реклама: доходи від бізнесів.
- Шантаж: тіньова механіка (НЕ впливає на репутацію журналіста).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import CorruptionLog, Player, PressBlackmail, PressInvestigation

logger = logging.getLogger("PressService")

# --- Константи ---
PRESS_EVIDENCE_PER_TICK = 0.08
PRESS_EVIDENCE_WHISTLEBLOWER_BONUS = 0.16
PRESS_PUBLISH_THRESHOLD = 0.7
HAPPINESS_IMPACT_PUBLISHED = -10
REPUTATION_IMPACT_PUBLISHED = -15
EVIDENCE_BONUS_ON_PUBLISH = 0.2
BLACKMAIL_DOUBLE_IMPACT = 2


def start_investigation(
    db: Session,
    journalist: Player,
    target: Player,
    incident_type: str = "corruption",
) -> dict:
    """Журналіст починає розслідування."""
    existing = (
        db.query(PressInvestigation)
        .filter(
            PressInvestigation.target_player_id == target.id,
            PressInvestigation.journalist_id == journalist.id,
            PressInvestigation.is_published.is_(False),
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Розслідування вже активне."}

    investigation = PressInvestigation(
        target_player_id=target.id,
        journalist_id=journalist.id,
        incident_type=incident_type,
        press_evidence=0.0,
        is_published=False,
        scale="local",
    )
    db.add(investigation)
    db.flush()
    logger.info("Розслідування почате: %s → %s", journalist.username, target.username)
    return {
        "success": True,
        "message": "Розслідування почате.",
        "investigation_id": str(investigation.id),
    }


def tick_investigation(
    db: Session,
    investigation: PressInvestigation,
    has_whistleblower: bool = False,
) -> dict:
    """Day tick — накопичення press_evidence."""
    increment = PRESS_EVIDENCE_WHISTLEBLOWER_BONUS if has_whistleblower else PRESS_EVIDENCE_PER_TICK
    investigation.press_evidence = min(1.0, float(investigation.press_evidence) + increment)
    db.flush()

    if investigation.press_evidence >= PRESS_PUBLISH_THRESHOLD:
        return {
            "success": True,
            "message": "Достатньо evidence для публікації.",
            "press_evidence": investigation.press_evidence,
            "can_publish": True,
        }
    return {
        "success": True,
        "message": f"Evidence: {investigation.press_evidence:.2f}.",
        "press_evidence": investigation.press_evidence,
        "can_publish": False,
    }


def publish_article(
    db: Session,
    investigation: PressInvestigation,
    target: Player,
    article_title: str | None = None,
) -> dict:
    """Публікація статті — впливає на happiness, репутацію, evidence."""
    if investigation.is_published:
        return {"success": False, "message": "Стаття вже опублікована."}

    if investigation.press_evidence < PRESS_PUBLISH_THRESHOLD:
        return {"success": False, "message": "Недостатньо evidence для публікації."}

    investigation.is_published = True
    investigation.published_at = datetime.now(UTC)
    investigation.article_title = article_title or "Скандал у місті!"
    investigation.happiness_impact = HAPPINESS_IMPACT_PUBLISHED
    investigation.reputation_impact = REPUTATION_IMPACT_PUBLISHED

    # Вплив на ціль
    if hasattr(target, "happiness"):
        target.happiness = max(0, (target.happiness or 0) + HAPPINESS_IMPACT_PUBLISHED)
    if hasattr(target, "reputation"):
        target.reputation = max(0, (target.reputation or 0) + REPUTATION_IMPACT_PUBLISHED)

    # Підвищуємо evidence_strength у corruption_log
    corruption = (
        db.query(CorruptionLog)
        .filter(CorruptionLog.perpetrator_id == target.id)
        .order_by(CorruptionLog.created_at.desc())
        .first()
    )
    if corruption:
        corruption.evidence_strength = min(1.0, float(corruption.evidence_strength) + EVIDENCE_BONUS_ON_PUBLISH)

    db.flush()
    logger.info("Стаття опублікована: %s", article_title)
    return {
        "success": True,
        "message": f"Стаття опублікована: {investigation.article_title}",
        "happiness_impact": HAPPINESS_IMPACT_PUBLISHED,
        "reputation_impact": REPUTATION_IMPACT_PUBLISHED,
    }


def offer_blackmail(
    db: Session,
    investigation: PressInvestigation,
    journalist: Player,
    target: Player,
    amount: Decimal,
) -> dict:
    """Журналіст пропонує шантаж цільовому гравцю."""
    if investigation.press_evidence < PRESS_PUBLISH_THRESHOLD:
        return {"success": False, "message": "Недостатньо evidence для шантажу."}

    if investigation.is_published:
        return {"success": False, "message": "Стаття вже опублікована."}

    blackmail = PressBlackmail(
        journalist_id=journalist.id,
        target_id=target.id,
        investigation_id=investigation.id,
        amount_demanded=amount,
        status="pending",
    )
    db.add(blackmail)
    db.flush()
    logger.info("Шантаж запропонований: %s → %s, сума=%s", journalist.username, target.username, amount)
    return {
        "success": True,
        "message": "Пропозиція шантажу надіслана.",
        "blackmail_id": str(blackmail.id),
    }


def respond_to_blackmail(
    db: Session,
    blackmail: PressBlackmail,
    target: Player,
    journalist: Player,
    investigation: PressInvestigation,
    action: str,  # accept|refuse|report_to_police
) -> dict:
    """Ціль відповідає на шантаж."""
    if blackmail.status != "pending":
        return {"success": False, "message": "Шантаж вже оброблений."}

    if action == "accept":
        # Ціль платить
        if Decimal(str(target.balance)) < Decimal(str(blackmail.amount_demanded)):
            return {"success": False, "message": "Недостатньо коштів."}
        target.balance = Decimal(str(target.balance)) - Decimal(str(blackmail.amount_demanded))
        journalist.balance = Decimal(str(journalist.balance)) + Decimal(str(blackmail.amount_demanded))
        blackmail.status = "accepted"
        blackmail.resolved_at = datetime.now(UTC)
        # Стаття стирається
        db.delete(investigation)
        db.flush()
        return {"success": True, "message": "Шантаж прийнято. Стаття знищена."}

    if action == "refuse":
        # Стаття публікується з подвійним впливом
        blackmail.status = "refused"
        blackmail.resolved_at = datetime.now(UTC)
        investigation.is_published = True
        investigation.published_at = datetime.now(UTC)
        investigation.happiness_impact = HAPPINESS_IMPACT_PUBLISHED * BLACKMAIL_DOUBLE_IMPACT
        investigation.reputation_impact = REPUTATION_IMPACT_PUBLISHED * BLACKMAIL_DOUBLE_IMPACT
        if hasattr(target, "happiness"):
            target.happiness = max(0, (target.happiness or 0) + investigation.happiness_impact)
        if hasattr(target, "reputation"):
            target.reputation = max(0, (target.reputation or 0) + investigation.reputation_impact)
        db.flush()
        return {"success": True, "message": "Шантаж відхилено. Стаття з подвійним впливом!"}

    if action == "report_to_police":
        # Повідомити в поліцію — шантаж є злочином
        blackmail.status = "reported_to_police"
        blackmail.resolved_at = datetime.now(UTC)
        # Створюємо corruption_log на журналіста
        corruption = CorruptionLog(
            incident_type="blackmail",
            perpetrator_id=journalist.id,
            victim_id=target.id,
            amount=float(blackmail.amount_demanded),
            evidence_strength=0.8,
            is_reported=True,
            is_investigated=False,
            is_proven=False,
        )
        db.add(corruption)
        db.flush()
        return {"success": True, "message": "Повідомлено в поліцію. Журналіст під розслідуванням."}

    return {"success": False, "message": "Невірна дія. Використайте: accept, refuse, report_to_police."}


def accept_advertising(
    db: Session,
    journalist: Player,
    advertiser: Player,
    amount: Decimal,
) -> dict:
    """Бізнес платить за рекламу у виданні."""
    if Decimal(str(advertiser.balance)) < amount:
        return {"success": False, "message": "Недостатньо коштів у рекламодавця."}

    advertiser.balance = Decimal(str(advertiser.balance)) - amount
    journalist.balance = Decimal(str(journalist.balance)) + amount
    db.flush()
    logger.info("Реклама: %s заплатив %s журналісту %s", advertiser.username, amount, journalist.username)
    return {"success": True, "message": f"Реклама розміщена. Дохід {amount}."}
