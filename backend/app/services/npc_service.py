"""
NPC-резиденти (Phase G2).

Полегшені NPC-акаунти — робітники і споживачі в районах. Не гравці:
не мають auth_token, не логіняться, не проходять onboarding. При звільненні
запис просто видаляється (як видалений акаунт).

Механіки:
- Генерація: мінімальна кількість для функціонування бізнесу (база з blueprint
  expected_jobs, зажата лімітом legal_form).
- Найм: гравець-власник наймає NPC за зарплату з cash_balance бізнесу.
- Звільнення: запис видаляється.
- ЗП і премія: двічі на місяць (ЗП 8-10 день, премія 20-23 день).
- Цикл витрат: рандомні дії з ймовірністю, баланс у коридорі
  (не банкрут, не накопичує).
- NPC входять у population району (див. district_metrics._district_population).
"""

from __future__ import annotations

import logging
import random
import uuid
from decimal import Decimal
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import Business, CityDistrict, NpcResident

logger = logging.getLogger("NpcService")

# --- Ліміти найму за legal_form ---
LEGAL_FORM_NPC_LIMITS: dict[str, int] = {
    "fop": 1,
    "tov": 5,
    "vat": 10,
}

# --- Параметри зарплати ---
DEFAULT_NPC_SALARY = Decimal("50.00")
DEFAULT_NPC_BONUS_PCT = Decimal("20.00")  # % від зарплати

# --- Параметри циклу витрат ---
NPC_BALANCE_MIN = Decimal("20.00")  # нижня межа коридору
NPC_BALANCE_MAX = Decimal("500.00")  # верхня межа коридору
NPC_DAILY_SPEND_MIN = Decimal("5.00")
NPC_DAILY_SPEND_MAX = Decimal("30.00")
NPC_SPEND_PROBABILITY = 0.7  # 70% шанс витрачати в день

# --- Параметри ЗП ---
SALARY_DAY_MIN = 8
SALARY_DAY_MAX = 10
BONUS_DAY_MIN = 20
BONUS_DAY_MAX = 23

# --- Базова зарплата за типом бізнесу ---
BASE_SALARY_BY_BUSINESS_TYPE: dict[str, Decimal] = {
    "shop": Decimal("40.00"),
    "factory": Decimal("55.00"),
    "utility_water": Decimal("60.00"),
    "utility_housing": Decimal("50.00"),
    "private_hostel": Decimal("35.00"),
}

LegalForm = Literal["fop", "tov", "vat"]


def get_npc_limit(legal_form: str) -> int:
    """Повертає максимальну кількість NPC для бізнесу за legal_form."""
    return LEGAL_FORM_NPC_LIMITS.get(legal_form, LEGAL_FORM_NPC_LIMITS["fop"])


def count_npcs_in_business(db: Session, business_id: uuid.UUID) -> int:
    """Кількість NPC, найнятих у бізнесі."""
    return db.query(func.count(NpcResident.id)).filter(NpcResident.workplace_business_id == business_id).scalar() or 0


def get_business_district_id(db: Session, business: Business) -> uuid.UUID | None:
    """Визначає district_id бізнесу через Building.

    Fallback: якщо бізнес без будівлі (муніципальний/seeded), використовує
    перший район міста — NPC все одно прив'язується до району для метрик.
    """
    building = business.building
    if building is not None:
        return building.district_id
    # Fallback: перший район міста (для муніципальних бізнесів без будівлі).
    district = (
        db.query(CityDistrict)
        .filter(CityDistrict.city_id == business.city_id)
        .order_by(CityDistrict.display_order)
        .first()
    )
    return district.id if district else None


def generate_npc_for_business(
    db: Session,
    business: Business,
    district_id: uuid.UUID,
    salary: Decimal | None = None,
) -> NpcResident | None:
    """Генерує і наймає NPC для бізнесу, якщо є вільний слот.

    Повертає створеного NpcResident або None, якщо ліміт досягнутий.
    """
    current_count = count_npcs_in_business(db, business.id)
    limit = get_npc_limit(business.legal_form)
    if current_count >= limit:
        return None

    if salary is None:
        salary = BASE_SALARY_BY_BUSINESS_TYPE.get(business.type, DEFAULT_NPC_SALARY)

    npc = NpcResident(
        city_id=business.city_id,
        district_id=district_id,
        workplace_business_id=business.id,
        cash_balance=Decimal("100.00"),  # стартовий баланс
        salary=salary,
        employed_at=func.now(),
        npc_type="worker",
    )
    db.add(npc)
    db.flush()
    logger.info(
        "NPC згенеровано для бізнесу %s (district=%s, salary=%s)",
        business.name,
        district_id,
        salary,
    )
    return npc


def dismiss_npc(db: Session, npc_id: uuid.UUID) -> bool:
    """Звільняє NPC — запис видаляється (як видалений акаунт).

    Повертає True якщо NPC був знайдений і видалений.
    """
    npc = db.query(NpcResident).filter(NpcResident.id == npc_id).first()
    if npc is None:
        return False
    db.delete(npc)
    db.flush()
    logger.info("NPC %s звільнено (видалено)", npc_id)
    return True


def list_business_npcs(db: Session, business_id: uuid.UUID) -> list[NpcResident]:
    """Повертає список NPC, найнятих у бізнесі."""
    return (
        db.query(NpcResident)
        .filter(NpcResident.workplace_business_id == business_id)
        .order_by(NpcResident.employed_at)
        .all()
    )


def ensure_minimal_npcs_for_business(db: Session, business: Business) -> list[NpcResident]:
    """Гарантує мінімальну кількість NPC для функціонування бізнесу.

    Мінімум = 1 NPC (або 0 якщо власник працює сам — це окрема механіка Phase G4).
    Для Phase G2: генеруємо 1 NPC для кожного активного бізнесу без жодного NPC.
    """
    district_id = get_business_district_id(db, business)
    if district_id is None:
        return []

    current = count_npcs_in_business(db, business.id)
    if current >= 1:
        return []

    npc = generate_npc_for_business(db, business, district_id)
    return [npc] if npc else []


def ensure_minimal_npcs_for_city(db: Session, city_id: uuid.UUID) -> int:
    """Гарантує мінімальну кількість NPC для всіх активних бізнесів міста.

    Повертає кількість створених NPC.
    """
    businesses = db.query(Business).filter(Business.city_id == city_id, Business.status == "active").all()
    created = 0
    for business in businesses:
        new_npcs = ensure_minimal_npcs_for_business(db, business)
        created += len(new_npcs)
    if created > 0:
        logger.info("Згенеровано %d NPC для міста %s", created, city_id)
    return created


# --- ЗП і премія ---


def _is_salary_day(game_day: int) -> bool:
    """ЗП виплачується 8-10 день місяця. Місяць = 30 ігрових днів."""
    day_of_month = (game_day % 30) + 1
    return SALARY_DAY_MIN <= day_of_month <= SALARY_DAY_MAX


def _is_bonus_day(game_day: int) -> bool:
    """Премія виплачується 20-23 день місяця."""
    day_of_month = (game_day % 30) + 1
    return BONUS_DAY_MIN <= day_of_month <= BONUS_DAY_MAX


def _already_paid_this_period(db: Session, npc: NpcResident, game_day: int, payment_type: str) -> bool:
    """Перевіряє, чи вже була виплата за цей період (за NPC немає окремої
    таблиці логів, тому використовуємо heuristic: employed_at + баланс).

    Для простоти Phase G2: виплачуємо один раз за період, перевіряючи
    що game_day потрапляє у вікно і npc.salary > 0.
    Повертає False (не платили) — реальну ідемпотентність забезпечує
    викликач (day tick викликається раз на день).
    """
    return False


def process_npc_payroll(db: Session, city_id: uuid.UUID, game_day: int) -> dict:
    """Виплачує ЗП (8-10 день) і премію (20-23 день) NPC міста.

    ЗП списується з cash_balance бізнесу, зарахується на cash_balance NPC.
    Якщо у бізнесу недостатньо коштів — NPC не отримує (борг не накопичується
    у Phase G2; Phase G5 (банк) додасть кредити).

    Повертає статистику.
    """
    is_salary = _is_salary_day(game_day)
    is_bonus = _is_bonus_day(game_day)
    if not is_salary and not is_bonus:
        return {"salary_paid": 0, "bonus_paid": 0, "total_paid": Decimal("0.00")}

    npcs = (
        db.query(NpcResident)
        .filter(NpcResident.city_id == city_id, NpcResident.workplace_business_id.isnot(None))
        .all()
    )

    salary_count = 0
    bonus_count = 0
    total_paid = Decimal("0.00")

    for npc in npcs:
        business = db.query(Business).filter(Business.id == npc.workplace_business_id).first()
        if business is None:
            continue

        if is_salary:
            amount = Decimal(str(npc.salary))
            if Decimal(str(business.cash_balance)) >= amount:
                business.cash_balance = Decimal(str(business.cash_balance)) - amount
                npc.cash_balance = Decimal(str(npc.cash_balance)) + amount
                salary_count += 1
                total_paid += amount

        if is_bonus:
            bonus_amount = (Decimal(str(npc.salary)) * DEFAULT_NPC_BONUS_PCT) / Decimal("100.00")
            if Decimal(str(business.cash_balance)) >= bonus_amount:
                business.cash_balance = Decimal(str(business.cash_balance)) - bonus_amount
                npc.cash_balance = Decimal(str(npc.cash_balance)) + bonus_amount
                bonus_count += 1
                total_paid += bonus_amount

    db.flush()
    logger.info(
        "NPC payroll день %d: ЗП=%d, премія=%d, всього=%s",
        game_day,
        salary_count,
        bonus_count,
        total_paid,
    )
    return {
        "salary_paid": salary_count,
        "bonus_paid": bonus_count,
        "total_paid": total_paid,
    }


# --- Цикл витрат ---


def process_npc_spending(db: Session, city_id: uuid.UUID, game_day: int) -> dict:
    """NPC витрачають гроші як споживачі — рандомні дії з ймовірністю.

    Баланс тримається в коридорі [NPC_BALANCE_MIN, NPC_BALANCE_MAX]:
    - Якщо баланс > MAX — витрачає обов'язково (скидає до ~MAX).
    - Якщо баланс < MIN — не витрачає (захист від банкрутства).
    - Інакше — витрачає з ймовірністю NPC_SPEND_PROBABILITY.

    Гроші списуються з cash_balance NPC (поки просто зникають з його балансу;
    Phase G4 прив'яже витрати до реальних бізнесів-гравців як доходи).
    """
    npcs = db.query(NpcResident).filter(NpcResident.city_id == city_id).all()

    spent_count = 0
    total_spent = Decimal("0.00")

    for npc in npcs:
        balance = Decimal(str(npc.cash_balance))

        # Захист від банкрутства
        if balance < NPC_BALANCE_MIN:
            continue

        # Обов'язкова витрата при перевищенні коридору
        if balance > NPC_BALANCE_MAX:
            spend_amount = (
                balance
                - NPC_BALANCE_MAX
                + Decimal(str(random.uniform(float(NPC_DAILY_SPEND_MIN), float(NPC_DAILY_SPEND_MAX))))
            )
        elif random.random() < NPC_SPEND_PROBABILITY:
            spend_amount = Decimal(str(random.uniform(float(NPC_DAILY_SPEND_MIN), float(NPC_DAILY_SPEND_MAX))))
        else:
            continue

        spend_amount = min(spend_amount, balance - NPC_BALANCE_MIN + Decimal("1.00"))
        if spend_amount <= 0:
            continue

        npc.cash_balance = balance - spend_amount
        spent_count += 1
        total_spent += spend_amount

    db.flush()
    return {"npcs_spent": spent_count, "total_spent": total_spent}


# --- API helpers ---


def hire_npc_for_business(
    db: Session,
    business: Business,
    salary: Decimal | None = None,
) -> dict:
    """Найм NPC для бізнесу. Повертає результат для API."""
    district_id = get_business_district_id(db, business)
    if district_id is None:
        return {"success": False, "message": "Бізнес не прив'язаний до району."}

    current = count_npcs_in_business(db, business.id)
    limit = get_npc_limit(business.legal_form)
    if current >= limit:
        return {
            "success": False,
            "message": f"Ліміт NPC досягнутий ({limit} для {business.legal_form.upper()}).",
        }

    npc = generate_npc_for_business(db, business, district_id, salary)
    if npc is None:
        return {"success": False, "message": "Не вдалося згенерувати NPC."}

    return {
        "success": True,
        "message": "NPC наймано.",
        "npc": {
            "id": str(npc.id),
            "salary": float(npc.salary),
            "cash_balance": float(npc.cash_balance),
            "npc_type": npc.npc_type,
        },
    }


def npc_to_dict(npc: NpcResident) -> dict:
    """Серіалізує NPC для API."""
    return {
        "id": str(npc.id),
        "district_id": str(npc.district_id),
        "workplace_business_id": str(npc.workplace_business_id) if npc.workplace_business_id else None,
        "cash_balance": float(npc.cash_balance),
        "salary": float(npc.salary),
        "npc_type": npc.npc_type,
        "employed_at": npc.employed_at.isoformat() if npc.employed_at else None,
    }
