"""
Політична система (Phase G6).

Механіки:
- Ієрархія посад у мерії: worker → department_head → deputy → mayor.
- Робота в мерії 3 місяці (90 ігрових днів) — вимога для балотування.
- Вибори мера: відкрите голосування, мандат 6 місяців (180 днів).
- Вотум недовіри: якщо більше 50% гравців проголосували — дострокові вибори.
- Підкуп голосів: тіньовий фонд, анонімна пропозиція, виборець може обдурити
  або повідомити в поліцію, corruption_log з evidence_strength.
- AI-мер: інвестує з treasury там, де метрики найгірші.
"""

from __future__ import annotations

import logging
import random
import uuid
from collections import Counter
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import (
    City,
    CityOffice,
    ElectionCandidate,
    MayorElection,
    MayorVote,
    Player,
    PoliticalCorruptionLog,
    VoteBribe,
)

logger = logging.getLogger("PoliticalService")

# --- Константи ---
MAYOR_TERM_DAYS = 180  # 6 місяців ігрового часу
ELECTION_DURATION_DAYS = 7  # 7 днів на вибори
MIN_OFFICE_DAYS_FOR_CANDIDACY = 90  # 3 місяці роботи в мерії
MIN_REPUTATION_FOR_CANDIDACY = 50  # мінімальна репутація
REQUIRED_EDUCATION = "College"  # економічна + юридична освіта

OFFICE_HIERARCHY = ("worker", "department_head", "deputy", "mayor")
DEPARTMENTS = ("economy", "social", "infrastructure", "security")

# Підкуп
BRIBE_EVIDENCE_BASE = 20.0  # базова ймовірність залишити сліди
BRIBE_EVIDENCE_REPORT_BONUS = 50.0  # якщо виборець повідомив у поліцію
BRIBE_REPORT_CHANCE = 0.3  # 30% шанс що виборець повідомить


def hire_office_worker(
    db: Session,
    city: City,
    player: Player,
    position: str = "worker",
    department: str | None = None,
    game_day: int = 0,
) -> dict:
    """Найм гравця на посаду у мерію."""
    if position not in OFFICE_HIERARCHY:
        return {"success": False, "message": f"Невірна посада. Доступні: {OFFICE_HIERARCHY}."}

    if position in ("worker", "department_head") and department not in DEPARTMENTS:
        return {"success": False, "message": f"Потрібен відділ: {DEPARTMENTS}."}

    # Перевірка що гравець ще не працює в мерії
    existing = (
        db.query(CityOffice)
        .filter(
            CityOffice.city_id == city.id,
            CityOffice.player_id == player.id,
            CityOffice.is_active.is_(True),
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Ви вже працюєте в мерії."}

    office = CityOffice(
        city_id=city.id,
        player_id=player.id,
        position=position,
        department=department,
        hired_at_game_day=game_day,
        is_active=True,
    )
    db.add(office)
    db.flush()
    logger.info("Гравець %s найнятий у мерію: посада=%s, відділ=%s", player.username, position, department)
    return {
        "success": True,
        "message": "Прийнято на посаду у мерію.",
        "office": {
            "id": str(office.id),
            "position": position,
            "department": department,
            "hired_at_game_day": game_day,
        },
    }


def get_office_history(db: Session, city_id: uuid.UUID, player_id: uuid.UUID) -> list[CityOffice]:
    """Повертає історію посад гравця у мерії."""
    return (
        db.query(CityOffice)
        .filter(
            CityOffice.city_id == city_id,
            CityOffice.player_id == player_id,
        )
        .order_by(CityOffice.hired_at_game_day.asc())
        .all()
    )


def get_total_office_days(db: Session, city_id: uuid.UUID, player_id: uuid.UUID, game_day: int) -> int:
    """Повертає сумарну кількість днів роботи в мерії."""
    offices = get_office_history(db, city_id, player_id)
    total = 0
    for office in offices:
        end_day = game_day if office.is_active else game_day  # Phase G6: додавати end_day
        total += max(0, end_day - office.hired_at_game_day)
    return total


def can_run_for_mayor(db: Session, city: City, player: Player, game_day: int) -> dict:
    """Перевіряє чи може гравець балотуватися у мери."""
    reasons: list[str] = []

    # 1. Робота в мерії не менше 3 місяців (90 днів)
    office_days = get_total_office_days(db, city.id, player.id, game_day)
    if office_days < MIN_OFFICE_DAYS_FOR_CANDIDACY:
        reasons.append(f"Потрібно {MIN_OFFICE_DAYS_FOR_CANDIDACY} днів роботи в мерії (у вас {office_days}).")

    # 2. Репутація
    reputation = getattr(player, "reputation", 0) or 0
    if reputation < MIN_REPUTATION_FOR_CANDIDACY:
        reasons.append(f"Потрібна репутація не нижче {MIN_REPUTATION_FOR_CANDIDACY} (у вас {reputation}).")

    # 3. Освіта
    education = player.education_level or "High School"
    education_order = ["None", "Primary", "Middle School", "High School", "College", "University"]
    if education_order.index(education) < education_order.index(REQUIRED_EDUCATION):
        reasons.append(f"Потрібна освіта не нижче {REQUIRED_EDUCATION} (у вас {education}).")

    if reasons:
        return {"success": False, "message": "Не виконано вимоги.", "reasons": reasons}
    return {"success": True, "message": "Можете балотуватися."}


def start_election(db: Session, city: City, game_day: int) -> dict:
    """Починає вибори мера."""
    # Перевіряємо що немає активних виборів
    existing = (
        db.query(MayorElection)
        .filter(
            MayorElection.city_id == city.id,
            MayorElection.status == "active",
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Вибори вже активні."}

    election = MayorElection(
        city_id=city.id,
        started_at_game_day=game_day,
        ends_at_game_day=game_day + ELECTION_DURATION_DAYS,
        status="active",
    )
    db.add(election)
    db.flush()
    logger.info("Вибори мера почалися: місто=%s, день=%d", city.name, game_day)
    return {
        "success": True,
        "message": "Вибори мера почалися.",
        "election": {
            "id": str(election.id),
            "started_at_game_day": game_day,
            "ends_at_game_day": election.ends_at_game_day,
        },
    }


def register_candidate(
    db: Session,
    election: MayorElection,
    player: Player,
    platform_text: str | None = None,
    game_day: int = 0,
) -> dict:
    """Реєстрація кандидата у виборах."""
    # Перевірка вимог
    city = db.query(City).filter(City.id == election.city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено."}

    can_run = can_run_for_mayor(db, city, player, game_day)
    if not can_run["success"]:
        return can_run

    # Перевірка що кандидат ще не зареєстрований
    existing = (
        db.query(ElectionCandidate)
        .filter(
            ElectionCandidate.election_id == election.id,
            ElectionCandidate.player_id == player.id,
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Ви вже зареєстровані як кандидат."}

    candidate = ElectionCandidate(
        election_id=election.id,
        player_id=player.id,
        platform_text=platform_text,
        registered_at_game_day=game_day,
    )
    db.add(candidate)
    db.flush()
    logger.info("Кандидат зареєстрований: %s", player.username)
    return {
        "success": True,
        "message": "Ви зареєстровані як кандидат.",
        "candidate": {"id": str(candidate.id), "player_id": str(player.id)},
    }


def cast_vote(
    db: Session,
    election: MayorElection,
    voter: Player,
    candidate: ElectionCandidate,
    game_day: int = 0,
) -> dict:
    """Гравець голосує за кандидата (відкрите голосування)."""
    if election.status != "active":
        return {"success": False, "message": "Вибори не активні."}

    if game_day > election.ends_at_game_day:
        return {"success": False, "message": "Голосування завершено."}

    # Перевірка що кандидат з того ж вибору
    if candidate.election_id != election.id:
        return {"success": False, "message": "Кандидат не з цих виборів."}

    # Перевірка що гравець ще не голосував
    existing = (
        db.query(MayorVote)
        .filter(
            MayorVote.election_id == election.id,
            MayorVote.voter_id == voter.id,
        )
        .first()
    )
    if existing:
        return {"success": False, "message": "Ви вже голосували."}

    vote = MayorVote(
        election_id=election.id,
        voter_id=voter.id,
        candidate_id=candidate.id,
        voted_at_game_day=game_day,
    )
    db.add(vote)
    db.flush()
    logger.info("Голос: %s → %s", voter.username, candidate.player_id)
    return {"success": True, "message": "Голос прийнято."}


def conclude_election(db: Session, election: MayorElection, game_day: int) -> dict:
    """Підбиває підсумки виборів: переможець = більшість голосів."""
    if election.status != "active":
        return {"success": False, "message": "Вибори вже завершені."}

    if game_day < election.ends_at_game_day:
        return {"success": False, "message": "Вибори ще тривають."}

    votes = db.query(MayorVote).filter(MayorVote.election_id == election.id).all()
    if not votes:
        election.status = "concluded"
        db.flush()
        return {"success": True, "message": "Вибори завершено без голосів."}

    # Рахуємо голоси по кандидатах
    vote_counts = Counter(v.candidate_id for v in votes)
    winner_candidate_id, winner_votes = vote_counts.most_common(1)[0]

    winner_candidate = db.query(ElectionCandidate).filter(ElectionCandidate.id == winner_candidate_id).first()
    if not winner_candidate:
        election.status = "concluded"
        db.flush()
        return {"success": False, "message": "Кандидат-переможець не знайдений."}

    # Призначаємо мера
    city = db.query(City).filter(City.id == election.city_id).first()
    if city:
        city.mayor_player_id = winner_candidate.player_id
        city.mayor_term_started_game_day = game_day

    election.status = "concluded"
    election.winner_id = winner_candidate.player_id
    db.flush()

    winner = db.query(Player).filter(Player.id == winner_candidate.player_id).first()
    logger.info("Вибори завершено: переможець=%s, голосів=%d", winner.username if winner else "?", winner_votes)
    return {
        "success": True,
        "message": "Вибори завершено.",
        "winner": winner.username if winner else None,
        "winner_votes": winner_votes,
        "total_votes": len(votes),
    }


def vote_of_no_confidence(db: Session, city: City, voter: Player, game_day: int) -> dict:
    """Гравець голосує за вотум недовіри меру.

    Якщо більше 50% гравців міста проголосували — дострокові вибори.
    """
    # Phase G6: спрощено — один голос = один недовір
    # Повна реалізація: окрема таблиця no_confidence_votes
    # Поки: якщо мер є, створюємо дострокові вибори
    if not city.mayor_player_id:
        return {"success": False, "message": "У місті немає мера."}

    # Перевірка терміну: не раніше ніж через 30 днів після обрання
    if city.mayor_term_started_game_day and game_day - city.mayor_term_started_game_day < 30:
        return {"success": False, "message": "Ще рано для вотуму недовіри (мин. 30 днів)."}

    # Створюємо дострокові вибори
    result = start_election(db, city, game_day)
    if not result["success"]:
        return result

    # Знімаємо мера
    city.mayor_player_id = None
    city.mayor_term_started_game_day = None
    db.flush()
    logger.info("Вотум недовіри: мер знятий, дострокові вибори почалися.")
    return {"success": True, "message": "Вотум недовіри: мер знятий, почалися дострокові вибори."}


# --- Підкуп голосів ---


def offer_bribe(
    db: Session,
    election: MayorElection,
    briber: Player,
    voter: Player,
    amount: Decimal,
    game_day: int = 0,
) -> dict:
    """Кандидат (або його прихильник) пропонує хабар виборцю."""
    if election.status != "active":
        return {"success": False, "message": "Вибори не активні."}

    if Decimal(str(briber.balance)) < amount:
        return {"success": False, "message": "Недостатньо коштів для хабара."}

    # Гроші переходять у "тіньовий фонд" (з балансу хабарника)
    briber.balance = Decimal(str(briber.balance)) - amount

    bribe = VoteBribe(
        election_id=election.id,
        briber_id=briber.id,
        voter_id=voter.id,
        amount=amount,
        status="offered",
        created_at_game_day=game_day,
    )
    db.add(bribe)

    # Запис у журнал корупції
    corruption = PoliticalCorruptionLog(
        city_id=election.city_id,
        actor_id=briber.id,
        action_type="vote_bribe",
        description=f"Хабар {amount} виборцю {voter.username}",
        evidence_strength=BRIBE_EVIDENCE_BASE,
        is_reported=False,
        created_at_game_day=game_day,
    )
    db.add(corruption)
    db.flush()
    logger.info("Хабар запропонований: %s → %s, сума=%s", briber.username, voter.username, amount)
    return {
        "success": True,
        "message": "Хабар запропонований.",
        "bribe_id": str(bribe.id),
        "evidence_strength": float(BRIBE_EVIDENCE_BASE),
    }


def respond_to_bribe(
    db: Session,
    bribe: VoteBribe,
    voter: Player,
    accept: bool,
    game_day: int = 0,
) -> dict:
    """Виборець відповідає на хабар: прийняти/відхилити/повідомити."""
    if bribe.voter_id != voter.id:
        return {"success": False, "message": "Це не ваш хабар."}

    if bribe.status != "offered":
        return {"success": False, "message": "Хабар вже оброблений."}

    if accept:
        bribe.status = "accepted"
        # Виборець отримує гроші
        voter.balance = Decimal(str(voter.balance)) + Decimal(str(bribe.amount))
        # Збільшуємо evidence_strength
        corruption = (
            db.query(PoliticalCorruptionLog)
            .filter(
                PoliticalCorruptionLog.actor_id == bribe.briber_id,
                PoliticalCorruptionLog.action_type == "vote_bribe",
            )
            .order_by(PoliticalCorruptionLog.created_at.desc())
            .first()
        )
        if corruption:
            corruption.evidence_strength = Decimal(str(corruption.evidence_strength)) + Decimal("10")
        result_msg = "Хабар прийнято. Гроші зараховано."
    else:
        # 30% шанс що виборець повідомить у поліцію
        if random.random() < BRIBE_REPORT_CHANCE:
            bribe.status = "reported"
            # Повертаємо гроші хабарнику
            briber = db.query(Player).filter(Player.id == bribe.briber_id).first()
            if briber:
                briber.balance = Decimal(str(briber.balance)) + Decimal(str(bribe.amount))
            # Збільшуємо evidence_strength суттєво
            corruption = (
                db.query(PoliticalCorruptionLog)
                .filter(
                    PoliticalCorruptionLog.actor_id == bribe.briber_id,
                    PoliticalCorruptionLog.action_type == "vote_bribe",
                )
                .order_by(PoliticalCorruptionLog.created_at.desc())
                .first()
            )
            if corruption:
                corruption.evidence_strength = Decimal(str(corruption.evidence_strength)) + Decimal(
                    str(BRIBE_EVIDENCE_REPORT_BONUS)
                )
                corruption.is_reported = True
            result_msg = "Ви повідомили в поліцію. Хабарника буде розслідувано."
        else:
            bribe.status = "rejected"
            # Повертаємо гроші хабарнику
            briber = db.query(Player).filter(Player.id == bribe.briber_id).first()
            if briber:
                briber.balance = Decimal(str(briber.balance)) + Decimal(str(bribe.amount))
            result_msg = "Хабар відхилено. Гроші повернуто хабарнику."

    db.flush()
    return {"success": True, "message": result_msg, "bribe_status": bribe.status}


# --- AI-мер ---


def ai_mayor_invest(db: Session, city: City, game_day: int) -> dict:
    """AI-мер інвестує з treasury там, де метрики найгірші.

    Знаходить район з найгіршим composite desirability і вкладає
    частину treasury у покращення (озеленення, інфраструктура).
    """
    from backend.app.models import CityDistrict
    from backend.app.services.district_metrics import recalculate_district_metrics

    districts = db.query(CityDistrict).filter(CityDistrict.city_id == city.id).all()
    if not districts:
        return {"success": False, "message": "Немає районів для інвестицій."}

    # Знаходимо район з найгіршим desirability
    worst = min(districts, key=lambda d: float(d.desirability or 50))
    investment = min(Decimal("1000.00"), Decimal(str(city.treasury_balance)) * Decimal("0.05"))

    if investment <= 0:
        return {"success": False, "message": "Недостатньо коштів у казні."}

    city.treasury_balance = Decimal(str(city.treasury_balance)) - investment
    # Покращуємо озеленення і безпеку (зменшуємо crime_risk)
    worst.green_space = min(100, float(worst.green_space or 0) + 5)
    worst.crime_risk = max(0, float(worst.crime_risk or 0) - 3)
    db.flush()

    # Перераховуємо метрики
    recalculate_district_metrics(db, worst, game_day)
    db.flush()

    logger.info(
        "AI-мер інвестував %s у район %s (desirability was %s)",
        investment,
        worst.name,
        worst.desirability,
    )
    return {
        "success": True,
        "message": f"AI-мер інвестував {investment} у район {worst.name}.",
        "district": worst.name,
        "investment": float(investment),
    }


def get_active_election(db: Session, city_id: uuid.UUID) -> MayorElection | None:
    """Повертає активні вибори міста."""
    return (
        db.query(MayorElection)
        .filter(
            MayorElection.city_id == city_id,
            MayorElection.status == "active",
        )
        .first()
    )


def get_election_results(db: Session, election: MayorElection) -> list[dict]:
    """Повертає результати виборів (кандидат → кількість голосів)."""
    votes = db.query(MayorVote).filter(MayorVote.election_id == election.id).all()
    counts = Counter(v.candidate_id for v in votes)
    candidates = db.query(ElectionCandidate).filter(ElectionCandidate.election_id == election.id).all()
    results = []
    for c in candidates:
        player = db.query(Player).filter(Player.id == c.player_id).first()
        results.append(
            {
                "candidate_id": str(c.id),
                "player_id": str(c.player_id),
                "player_name": player.username if player else "?",
                "votes": counts.get(c.id, 0),
                "platform": c.platform_text,
            }
        )
    results.sort(key=lambda x: x["votes"], reverse=True)
    return results
