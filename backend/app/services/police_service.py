"""
Поліцейська система (Phase G8).

Механіки:
- Ієрархія: Patrol → Detective → Chief.
- Патрулювання району: випадкові події (штраф, evidence, хабарна пропозиція).
- Детектив: доступ до corruption_log, підвищення evidence_strength, арешт.
- Chief: розподіл патрульних, бюджет, призначається мером.
- Хабар: поліцейський може взяти → corruption_log на себе.
"""

from __future__ import annotations

import logging
import random
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import (
    City,
    CityDistrict,
    CorruptionLog,
    Player,
    PoliceOfficer,
    PoliceRecord,
)

logger = logging.getLogger("PoliceService")

# --- Константи ---
POLICE_RANKS = ("patrol", "detective", "chief")
PROMOTION_INVESTIGATIONS = 5  # стільки успішних розслідувань для підвищення
BRIBE_EVIDENCE_ON_TAKE = 0.4  # evidence на поліцейського при взятті хабаря
FINE_AMOUNT_DEFAULT = Decimal("100.00")
ARREST_DURATION_DAYS = 1  # блокує дії на 1 ігровий день


def hire_police_officer(
    db: Session,
    city: City,
    player: Player,
    game_day: int = 0,
) -> dict:
    """Найм гравця в поліцію на посаду patrol."""
    existing = (
        db.query(PoliceOfficer)
        .filter(
            PoliceOfficer.city_id == city.id,
            PoliceOfficer.player_id == player.id,
            PoliceOfficer.is_active.is_(True),
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Ви вже працюєте в поліції."}

    # Перевірка що немає active chief (тільки один)
    officer = PoliceOfficer(
        city_id=city.id,
        player_id=player.id,
        rank="patrol",
        hired_at_game_day=game_day,
        is_active=True,
    )
    db.add(officer)
    db.flush()
    logger.info("Гравець %s найнятий у поліцію (patrol)", player.username)
    return {
        "success": True,
        "message": "Прийнято у поліцію на посаду patrol.",
        "officer_id": str(officer.id),
    }


def get_officer(db: Session, city_id: uuid.UUID, player_id: uuid.UUID) -> PoliceOfficer | None:
    """Повертає активного поліцейського гравця."""
    return (
        db.query(PoliceOfficer)
        .filter(
            PoliceOfficer.city_id == city_id,
            PoliceOfficer.player_id == player_id,
            PoliceOfficer.is_active.is_(True),
        )
        .first()
    )


def promote_officer(db: Session, officer: PoliceOfficer, game_day: int) -> dict:
    """Підвищення поліцейського: patrol → detective."""
    if officer.rank != "patrol":
        return {"success": False, "message": "Тільки patrol можна підвищити до detective."}

    if officer.successful_investigations < PROMOTION_INVESTIGATIONS:
        return {
            "success": False,
            "message": f"Потрібно {PROMOTION_INVESTIGATIONS} успішних розслідувань "
            f"(у вас {officer.successful_investigations}).",
        }

    officer.rank = "detective"
    officer.promoted_at_game_day = game_day
    db.flush()
    logger.info("Поліцейський підвищений до detective")
    return {"success": True, "message": "Підвищено до detective.", "rank": "detective"}


def appoint_chief(
    db: Session,
    city: City,
    mayor: Player,
    candidate: Player,
    game_day: int,
) -> dict:
    """Мер призначає начальника поліції (один раз за термін)."""
    if city.mayor_player_id != mayor.id:
        return {"success": False, "message": "Тільки мер може призначати начальника поліції."}

    # Кандидат має бути діючим або колишнім поліцейським з 90 днів стажу
    officer = (
        db.query(PoliceOfficer)
        .filter(
            PoliceOfficer.city_id == city.id,
            PoliceOfficer.player_id == candidate.id,
        )
        .order_by(PoliceOfficer.hired_at_game_day.asc())
        .first()
    )
    if not officer:
        return {"success": False, "message": "Кандидат не є поліцейським."}

    total_days = game_day - officer.hired_at_game_day
    if total_days < 90:
        return {"success": False, "message": f"Потрібно 90 днів стажу (у кандидата {total_days})."}

    # Знімаємо поточного chief
    current_chief = (
        db.query(PoliceOfficer)
        .filter(
            PoliceOfficer.city_id == city.id,
            PoliceOfficer.rank == "chief",
            PoliceOfficer.is_active.is_(True),
        )
        .first()
    )
    if current_chief:
        current_chief.is_active = False

    # Призначаємо нового
    officer.rank = "chief"
    officer.appointed_by_mayor_id = mayor.id
    officer.promoted_at_game_day = game_day
    officer.is_active = True
    db.flush()
    logger.info("Начальник поліції призначений: %s", candidate.username)
    return {"success": True, "message": "Начальник поліції призначений.", "chief_id": str(officer.id)}


def patrol_district(
    db: Session,
    officer: PoliceOfficer,
    district: CityDistrict,
    game_day: int,
) -> dict:
    """Патрулювання району — випадкові події."""
    if officer.rank not in ("patrol", "detective", "chief"):
        return {"success": False, "message": "Невірна посада."}

    officer.patrol_district_id = district.id
    db.flush()

    # Ймовірність події залежить від crime_risk
    crime_risk = float(district.crime_risk or 0) / 100.0
    event_chance = min(0.8, 0.2 + crime_risk * 0.6)

    if random.random() > event_chance:
        return {"success": True, "message": "Патруль завершено: нічого не виявлено.", "event": "empty"}

    # Випадкова подія
    events = ("minor_offense", "suspicious_transaction", "bribe_offer", "nothing")
    weights = [0.4, 0.2, 0.2, 0.2]
    event = random.choices(events, weights=weights, k=1)[0]

    if event == "minor_offense":
        # Штраф у treasury
        fine = FINE_AMOUNT_DEFAULT
        # Створюємо police_record на випадкового NPC (спрощено)
        record = PoliceRecord(
            player_id=officer.player_id,  # спрощено: запис на патрульного
            offense_type="minor_offense",
            fine_amount=fine,
            status="fined",
        )
        db.add(record)
        officer.successful_investigations += 1
        db.flush()
        return {
            "success": True,
            "message": f"Виявлено дрібне правопорушення. Штраф {fine}.",
            "event": "minor_offense",
            "fine": float(fine),
        }

    if event == "suspicious_transaction":
        # Додаємо evidence до випадкового corruption_log
        corruption = (
            db.query(CorruptionLog)
            .filter(CorruptionLog.is_proven.is_(False))
            .order_by(CorruptionLog.created_at.desc())
            .first()
        )
        if corruption:
            corruption.evidence_strength = min(1.0, float(corruption.evidence_strength) + 0.1)
            corruption.is_investigated = True
            officer.successful_investigations += 1
            db.flush()
            return {
                "success": True,
                "message": "Виявлено підозрілу транзакцію. Evidence +0.1.",
                "event": "suspicious_transaction",
            }
        return {"success": True, "message": "Підозріла транзакція, але справ немає.", "event": "suspicious_transaction"}

    if event == "bribe_offer":
        # NPC пропонує хабар — повертаємо інформацію, гравець обирає
        bribe_amount = Decimal("200.00")
        return {
            "success": True,
            "message": f"NPC пропонує хабар {bribe_amount}. Використайте /police/accept-bribe або /police/refuse-bribe.",
            "event": "bribe_offer",
            "bribe_amount": float(bribe_amount),
        }

    return {"success": True, "message": "Патруль завершено.", "event": "nothing"}


def accept_bribe(
    db: Session,
    officer: PoliceOfficer,
    player: Player,
    amount: Decimal,
    game_day: int,
) -> dict:
    """Поліцейський бере хабар → гроші + corruption_log на себе."""
    player.balance = Decimal(str(player.balance)) + amount
    officer.bribes_taken += 1

    corruption = CorruptionLog(
        incident_type="police_bribe",
        perpetrator_id=player.id,
        amount=float(amount),
        evidence_strength=BRIBE_EVIDENCE_ON_TAKE,
        is_reported=False,
        is_investigated=False,
        is_proven=False,
    )
    db.add(corruption)
    db.flush()
    logger.info("Поліцейський %s взяв хабар %s", player.username, amount)
    return {
        "success": True,
        "message": f"Хабар {amount} прийнято. Увага: створено corruption_log.",
        "evidence_strength": BRIBE_EVIDENCE_ON_TAKE,
    }


def refuse_bribe(
    db: Session,
    officer: PoliceOfficer,
) -> dict:
    """Поліцейський відмовляє від хабаря — +репутація."""
    officer.successful_investigations += 1
    db.flush()
    return {"success": True, "message": "Хабар відхилено. Чесна служба."}


def arrest_player(
    db: Session,
    officer: PoliceOfficer,
    target: Player,
    game_day: int,
) -> dict:
    """Детектив арештовує гравця (блокує на 1 ігровий день)."""
    if officer.rank not in ("detective", "chief"):
        return {"success": False, "message": "Тільки detective або chief можуть арештовувати."}

    record = PoliceRecord(
        player_id=target.id,
        offense_type="arrest",
        fine_amount=None,
        status="imprisoned",
    )
    db.add(record)
    officer.successful_investigations += 1
    db.flush()
    logger.info("Гравець %s арештований поліцейським %s", target.username, officer.player_id)
    return {"success": True, "message": f"Гравець {target.username} арештований на {ARREST_DURATION_DAYS} день."}


def confiscate_business(
    db: Session,
    officer: PoliceOfficer,
    business_id: uuid.UUID,
    game_day: int,
) -> dict:
    """Конфіскація бізнесу за рішенням суду (спрощено)."""
    from backend.app.models import Business

    if officer.rank != "chief":
        return {"success": False, "message": "Тільки chief може конфіскувати бізнес."}

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return {"success": False, "message": "Бізнес не знайдено."}

    business.status = "closed"
    db.flush()
    logger.info("Бізнес %s конфісковано", business.name)
    return {"success": True, "message": f"Бізнес {business.name} конфісковано."}


def get_corruption_log_access(db: Session, officer: PoliceOfficer, city_id: uuid.UUID) -> list[dict]:
    """Детектив/chief має доступ до corruption_log."""
    if officer.rank not in ("detective", "chief"):
        return []

    logs = (
        db.query(CorruptionLog)
        .filter(CorruptionLog.is_proven.is_(False))
        .order_by(CorruptionLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": str(log.id),
            "incident_type": log.incident_type,
            "evidence_strength": float(log.evidence_strength),
            "is_investigated": log.is_investigated,
            "is_proven": log.is_proven,
        }
        for log in logs
    ]
