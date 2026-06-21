"""
Вакансії та найм (Phase G4).

Механіки:
- Фіксована ЗП за типом бізнесу (почасова статична).
- Премія % від чистого прибутку — власник виставляє (bonus_pct).
- Гравець-власник може працювати сам (витрачає енергію, без ЗП — дивіденди).
- Звільнення гравця-працівника за бажанням власника.
- Біржа "для студентів" (очна освіта — лише вечірні зміни).
- NPC-позиції (is_npc_position) відрізняються від гравець-вакансій.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, Job, Player

logger = logging.getLogger("VacancyService")

# --- Фіксована ЗП за типом бізнесу (почасова) ---
FIXED_SALARY_BY_BUSINESS_TYPE: dict[str, Decimal] = {
    "shop": Decimal("25.00"),
    "factory": Decimal("35.00"),
    "utility_power": Decimal("40.00"),
    "utility_water": Decimal("38.00"),
    "utility_housing": Decimal("30.00"),
    "utility_waste": Decimal("32.00"),
    "private_hostel": Decimal("20.00"),
}
DEFAULT_FIXED_SALARY = Decimal("25.00")

# --- Енергія за зміну ---
DEFAULT_ENERGY_COST = 30
EVENING_SHIFT_ENERGY_COST = 25  # для студентів

# --- Премія за замовчуванням ---
DEFAULT_BONUS_PCT = Decimal("10.00")
MAX_BONUS_PCT = Decimal("50.00")

ShiftType = str  # "day", "evening", "student"


def get_fixed_salary(business_type: str) -> Decimal:
    """Повертає фіксовану погодинну ЗП для типу бізнесу."""
    return FIXED_SALARY_BY_BUSINESS_TYPE.get(business_type, DEFAULT_FIXED_SALARY)


def post_player_vacancy(
    db: Session,
    business: Business,
    *,
    title: str | None = None,
    bonus_pct: Decimal = DEFAULT_BONUS_PCT,
    shift_type: ShiftType = "day",
    min_education: str = "High School",
) -> dict:
    """Власник виставляє вакансію для гравця-працівника.

    ЗП фіксована за типом бізнесу. Премію власник виставляє у %.
    """
    if bonus_pct < 0 or bonus_pct > MAX_BONUS_PCT:
        return {
            "success": False,
            "message": f"Премія має бути від 0 до {MAX_BONUS_PCT}%.",
        }

    salary = get_fixed_salary(business.type)
    energy_cost = EVENING_SHIFT_ENERGY_COST if shift_type == "student" else DEFAULT_ENERGY_COST

    job = Job(
        business_id=business.id,
        title=title or f"Працівник {business.name}",
        salary_per_hour=salary,
        min_education=min_education,
        energy_cost_per_shift=energy_cost,
        bonus_pct=bonus_pct,
        shift_type=shift_type,
        is_npc_position=False,
    )
    db.add(job)
    db.flush()
    logger.info(
        "Вакансія виставлена: %s (ЗП=%s/год, премія=%s%%, зміна=%s)",
        job.title,
        salary,
        bonus_pct,
        shift_type,
    )
    return {
        "success": True,
        "message": "Вакансію виставлено.",
        "job": {
            "id": str(job.id),
            "title": job.title,
            "salary_per_hour": float(salary),
            "bonus_pct": float(bonus_pct),
            "shift_type": shift_type,
            "min_education": min_education,
        },
    }


def apply_for_job(db: Session, job: Job, player: Player) -> dict:
    """Гравець подає заявку на вакансію.

    Перевіряє: вакансія вільна, освіта відповідає, гравець не має іншої роботи.
    """
    if job.filled_by_player_id is not None:
        return {"success": False, "message": "Вакансія вже зайнята."}

    if job.is_npc_position:
        return {"success": False, "message": "Ця позиція тільки для NPC."}

    # Перевірка що гравець не має іншої роботи (пряим запитом, а не через relationship)
    existing_job = db.query(Job).filter(Job.filled_by_player_id == player.id).first()
    if existing_job is not None:
        return {"success": False, "message": "Ви вже працюєте. Спочатку звільніться."}

    # Перевірка освіти
    education_order = ["None", "Primary", "Middle School", "High School", "College", "University"]
    player_edu = player.education_level or "High School"
    if education_order.index(player_edu) < education_order.index(job.min_education):
        return {
            "success": False,
            "message": f"Потрібна освіта не нижче {job.min_education}.",
        }

    # Перевірка зміни для студентів
    if job.shift_type == "student":
        # Phase G6: перевірка що гравець студент (очна освіта)
        # Поки дозволяємо всім — студенти визначаються в Phase G6
        pass

    job.filled_by_player_id = player.id
    db.flush()
    logger.info("Гравець %s найнятий на вакансію %s", player.username, job.title)
    return {
        "success": True,
        "message": "Ви прийнятий на роботу.",
        "job": {
            "id": str(job.id),
            "title": job.title,
            "salary_per_hour": float(job.salary_per_hour),
            "bonus_pct": float(job.bonus_pct),
            "shift_type": job.shift_type,
        },
    }


def fire_player(db: Session, job: Job, owner: Player) -> dict:
    """Власник звільняє гравця-працівника."""
    if job.filled_by_player_id is None:
        return {"success": False, "message": "Вакансія не зайнята."}

    business = db.query(Business).filter(Business.id == job.business_id).first()
    if business is None or business.owner_player_id != owner.id:
        return {"success": False, "message": "Ви не власник цього бізнесу."}

    fired_player_id = job.filled_by_player_id
    job.filled_by_player_id = None
    db.flush()
    logger.info("Гравець %s звільнений з вакансії %s", fired_player_id, job.title)
    return {"success": True, "message": "Працівника звільнено."}


def owner_works_shift(db: Session, business: Business, owner: Player) -> dict:
    """Власник працює у власному бізнесі — витрачає енергію, без ЗП.

    На відміну від найманого працівника, власник не отримує ЗП —
    він має доступ до cash_balance бізнесу (дивіденди/прибуток).
    """
    if business.owner_player_id != owner.id:
        return {"success": False, "message": "Ви не власник цього бізнесу."}

    if owner.energy < DEFAULT_ENERGY_COST:
        return {"success": False, "message": "Недостатньо енергії для зміни."}

    owner.energy -= DEFAULT_ENERGY_COST
    db.flush()
    logger.info("Власник %s відпрацював зміну у %s", owner.username, business.name)
    return {
        "success": True,
        "message": "Ви відпрацювали зміну.",
        "energy_spent": DEFAULT_ENERGY_COST,
        "energy_remaining": owner.energy,
    }


def list_open_vacancies(db: Session, city_id: uuid.UUID | None = None) -> list[Job]:
    """Повертає всі відкриті вакансії (не зайняті, не NPC-позиції)."""
    query = db.query(Job).filter(
        Job.filled_by_player_id.is_(None),
        Job.is_npc_position.is_(False),
    )
    if city_id is not None:
        query = query.join(Business).filter(Business.city_id == city_id)
    return query.order_by(Job.created_at.desc()).all()


def list_student_vacancies(db: Session, city_id: uuid.UUID | None = None) -> list[Job]:
    """Повертає вакансії для студентів (вечірні зміни)."""
    query = db.query(Job).filter(
        Job.filled_by_player_id.is_(None),
        Job.is_npc_position.is_(False),
        Job.shift_type == "student",
    )
    if city_id is not None:
        query = query.join(Business).filter(Business.city_id == city_id)
    return query.all()


def job_to_dict(job: Job, *, include_business: bool = False) -> dict:
    """Серіалізує вакансію для API."""
    d = {
        "id": str(job.id),
        "business_id": str(job.business_id),
        "title": job.title,
        "salary_per_hour": float(job.salary_per_hour),
        "min_education": job.min_education,
        "energy_cost_per_shift": job.energy_cost_per_shift,
        "bonus_pct": float(job.bonus_pct),
        "shift_type": job.shift_type,
        "is_npc_position": job.is_npc_position,
        "filled_by_player_id": str(job.filled_by_player_id) if job.filled_by_player_id else None,
    }
    if include_business and job.business:
        d["business_name"] = job.business.name
        d["business_type"] = job.business.type
    return d
