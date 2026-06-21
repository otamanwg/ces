"""
Судова система (Phase G8).

Механіки:
- Автоматичний вердикт за evidence_strength.
- Апеляція: 3 AI-судді з corruption_resistance.
- Підкуп суддів: успіх → суддя голосує "overturn", 2/3 → скасувати.
- Невдалий хабар → подвоєне покарання + новий corruption_log.
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import CorruptionLog, CourtCase, Player, PrisonSentence

logger = logging.getLogger("CourtService")

# --- Константи ---
APPEAL_DEADLINE_DAYS = 3  # ігрових днів на апеляцію
JUDGE_RESISTANCE_MIN = 0.3
JUDGE_RESISTANCE_MAX = 0.9
BRIBE_SUCCESS_THRESHOLD = 0.5  # якщо amount/bribe_base > resistance → успіх

VERDICT_FINE = "fine"
VERDICT_LICENSE_REVOKED = "license_revoked"
VERDICT_CANDIDACY_REVOKED = "candidacy_revoked"
VERDICT_MANDATE_REVOKED = "mandate_revoked"
VERDICT_CRIMINAL_CASE = "criminal_case"
VERDICT_AQUITTED = "acquitted"

# Тривалість ув'язнення (ігрові дні)
PRISON_DAYS_MINOR = (3, 7)
PRISON_DAYS_MEDIUM = (14, 30)
PRISON_DAYS_HEAVY = (60, 90)


def determine_verdict(evidence_strength: float, incident_type: str) -> str:
    """Визначає вердикт за evidence_strength і типом інциденту."""
    if evidence_strength < 0.7:
        return VERDICT_AQUITTED
    if evidence_strength < 0.8:
        return VERDICT_FINE
    if evidence_strength < 0.9:
        if incident_type in ("vote_bribe", "election_fraud"):
            return VERDICT_CANDIDACY_REVOKED
        return VERDICT_LICENSE_REVOKED
    # 0.9-1.0
    if incident_type in ("vote_bribe", "election_fraud"):
        return VERDICT_MANDATE_REVOKED
    return VERDICT_CRIMINAL_CASE


def create_court_case(
    db: Session,
    corruption_log: CorruptionLog,
    defendant: Player,
    game_day: int,
) -> dict:
    """Створює судову справу з автоматичним вердиктом."""
    verdict = determine_verdict(float(corruption_log.evidence_strength), corruption_log.incident_type)

    case = CourtCase(
        corruption_log_id=corruption_log.id,
        defendant_id=defendant.id,
        verdict=verdict,
        is_appealed=False,
        appeal_deadline=datetime.now(UTC) + timedelta(days=APPEAL_DEADLINE_DAYS),
    )
    db.add(case)

    # Позначаємо corruption_log як proven
    corruption_log.is_proven = True
    db.flush()

    # Якщо criminal_case — створюємо prison_sentence
    if verdict == VERDICT_CRIMINAL_CASE:
        days = _prison_days_for_incident(corruption_log.incident_type)
        sentence = PrisonSentence(
            player_id=defendant.id,
            court_case_id=case.id,
            days_total=days,
            days_served=0,
            days_remaining=days,
            business_impact="none",
            status="serving",
        )
        db.add(sentence)
        db.flush()
        logger.info("Створено тюремне ув'язнення: %s днів для %s", days, defendant.username)
        return {
            "success": True,
            "message": f"Вердикт: {verdict}. Ув'язнення на {days} днів.",
            "case_id": str(case.id),
            "verdict": verdict,
            "prison_days": days,
        }

    logger.info("Створено судову справу: вердикт=%s", verdict)
    return {
        "success": True,
        "message": f"Вердикт: {verdict}.",
        "case_id": str(case.id),
        "verdict": verdict,
    }


def _prison_days_for_incident(incident_type: str) -> int:
    """Визначає тривалість ув'язнення за типом інциденту."""
    if incident_type in ("police_bribe", "minor_bribe"):
        return random.randint(*PRISON_DAYS_MINOR)
    if incident_type in ("vote_bribe", "blackmail", "judge_bribe"):
        return random.randint(*PRISON_DAYS_MEDIUM)
    return random.randint(*PRISON_DAYS_HEAVY)


def file_appeal(
    db: Session,
    case: CourtCase,
    player: Player,
    game_day: int,
) -> dict:
    """Гравець подає апеляцію."""
    if case.is_appealed:
        return {"success": False, "message": "Апеляція вже подана."}

    if case.appeal_deadline and datetime.now(UTC) > case.appeal_deadline:
        return {"success": False, "message": "Дедлайн апеляції минув."}

    case.is_appealed = True
    # Генеруємо 3 судді з corruption_resistance
    case.judge_1_vote = "undecided"
    case.judge_2_vote = "undecided"
    case.judge_3_vote = "undecided"
    db.flush()
    logger.info("Апеляція подана для справи %s", case.id)
    return {
        "success": True,
        "message": "Апеляція подана. 3 судді розглядають справу.",
        "case_id": str(case.id),
    }


def bribe_judge(
    db: Session,
    case: CourtCase,
    player: Player,
    judge_number: int,  # 1, 2, 3
    amount: Decimal,
    game_day: int,
) -> dict:
    """Гравець підкуповує суддю."""
    if not case.is_appealed:
        return {"success": False, "message": "Апеляція не подана."}

    if judge_number not in (1, 2, 3):
        return {"success": False, "message": "Невірний номер судді (1-3)."}

    # Перевіряємо чи суддя вже підкуплений
    bribed_attr = f"judge_{judge_number}_bribed"
    if getattr(case, bribed_attr):
        return {"success": False, "message": f"Суддя {judge_number} вже підкуплений."}

    if Decimal(str(player.balance)) < amount:
        return {"success": False, "message": "Недостатньо коштів."}

    # Генеруємо resistance судді (рандомний 0.3-0.9)
    resistance = random.uniform(JUDGE_RESISTANCE_MIN, JUDGE_RESISTANCE_MAX)
    # Чим більша сума відносно бази, тим вищий шанс
    bribe_base = Decimal("1000.00")
    success_ratio = float(amount / bribe_base)

    player.balance = Decimal(str(player.balance)) - amount

    if success_ratio > resistance:
        # Успішний хабар
        setattr(case, bribed_attr, True)
        setattr(case, f"judge_{judge_number}_vote", "overturn")
        db.flush()
        logger.info("Суддя %d підкуплений (resistance=%.2f)", judge_number, resistance)
        # Перевіряємо чи всі 3 проголосували
        return _check_appeal_result(db, case, player, game_day)
    else:
        # Невдалий хабар → подвоєне покарання
        setattr(case, f"judge_{judge_number}_vote", "uphold")
        # Створюємо новий corruption_log на гравця
        corruption = CorruptionLog(
            incident_type="judge_bribe",
            perpetrator_id=player.id,
            amount=float(amount),
            evidence_strength=0.9,
            is_reported=True,
            is_investigated=True,
            is_proven=True,
        )
        db.add(corruption)
        db.flush()

        # Подвоюємо покарання
        _double_punishment(db, case, player, game_day)
        logger.info("Невдалий хабар судді %d (resistance=%.2f) — подвоєне покарання", judge_number, resistance)
        return {
            "success": False,
            "message": f"Невдалий хабар судді {judge_number}! Подвоєне покарання.",
            "resistance": resistance,
        }


def _check_appeal_result(db: Session, case: CourtCase, player: Player, game_day: int) -> dict:
    """Перевіряє чи апеляція завершена (всі 3 судді проголосували)."""
    votes = [case.judge_1_vote, case.judge_2_vote, case.judge_3_vote]
    if any(v == "undecided" or v is None for v in votes):
        return {
            "success": True,
            "message": "Суддя підкуплений. Очікуємо решту голосів.",
            "votes": votes,
        }

    # Рахуємо
    overturn_count = sum(1 for v in votes if v == "overturn")
    if overturn_count >= 2:
        # Вердикт скасовано
        case.final_verdict = VERDICT_AQUITTED
        # Звільняємо з тюрми якщо є
        sentence = (
            db.query(PrisonSentence)
            .filter(
                PrisonSentence.player_id == player.id,
                PrisonSentence.court_case_id == case.id,
                PrisonSentence.status == "serving",
            )
            .first()
        )
        if sentence:
            sentence.status = "released"
            sentence.released_at = datetime.utcnow()
        db.flush()
        return {
            "success": True,
            "message": "Апеляція успішна! Вердикт скасовано (2/3 суддів).",
            "final_verdict": VERDICT_AQUITTED,
        }
    else:
        # Вердикт залишено
        case.final_verdict = case.verdict
        db.flush()
        return {
            "success": True,
            "message": f"Апеляція відхилена. Вердикт залишено: {case.verdict}.",
            "final_verdict": case.verdict,
        }


def _double_punishment(db: Session, case: CourtCase, player: Player, game_day: int) -> None:
    """Подвоює покарання за невдалий хабар."""
    sentence = (
        db.query(PrisonSentence)
        .filter(
            PrisonSentence.player_id == player.id,
            PrisonSentence.court_case_id == case.id,
            PrisonSentence.status == "serving",
        )
        .first()
    )
    if sentence:
        sentence.days_total = sentence.days_total * 2
        sentence.days_remaining = sentence.days_remaining * 2
        db.flush()
