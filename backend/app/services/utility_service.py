"""
Комунальні служби як бізнеси (Phase G3).

Механіки:
- Utility-бізнеси (power/water/waste) мають service_capacity і service_load.
- Комунальні платежі: кожен активний бізнес міста платить щодня комунальним
  службам за послуги. Служби платять податки у казну, мають свій баланс.
- Bankruptcy: якщо utility-служба банкротиться → тригер тендеру → 1 ігровий
  день без сервісу → екстрений контракт з сусіднім містом за завищеними цінами.
  Різницю платить мерія (з казни), це руйнує рейтинг мера.
- Попередження у мера: якщо service_load > 80% capacity або служба банкрот.

Інтеграція з district_metrics: реальні потужності utility-бізнесів замінюють
базові 100 у формулах power_supply/water_supply/waste_management.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models import Business, City, UtilityEmergencyContract

logger = logging.getLogger("UtilityService")

# --- Константи ---

# Комунальний платіж за типом бізнесу (щоденний, з cash_balance бізнеса).
UTILITY_FEE_BY_BUSINESS_TYPE: dict[str, Decimal] = {
    "shop": Decimal("5.00"),
    "factory": Decimal("15.00"),
    "utility_power": Decimal("10.00"),
    "utility_water": Decimal("8.00"),
    "utility_housing": Decimal("12.00"),
    "utility_waste": Decimal("7.00"),
    "private_hostel": Decimal("6.00"),
}
DEFAULT_UTILITY_FEE = Decimal("5.00")

# Податок на прибуток utility-служб (у казну).
UTILITY_TAX_RATE = Decimal("0.10")  # 10%

# Екстрений контракт: завищення ціни.
EMERGENCY_PRICE_MULTIPLIER = Decimal("3.0")
NORMAL_PRICE_PER_UNIT = {
    "power": Decimal("0.50"),
    "water": Decimal("0.30"),
    "waste": Decimal("0.25"),
    "housing": Decimal("0.40"),
}

# Пороги для попереджень.
LOAD_WARNING_THRESHOLD = 0.8  # 80% від capacity
LOW_BALANCE_WARNING = Decimal("500.00")  # нижче цього — попередження

UTILITY_SERVICE_TYPES = ("power", "water", "waste", "housing")


@dataclass
class UtilityServiceStatus:
    service_type: str
    active_businesses: int
    total_capacity: float
    total_load: float
    load_ratio: float
    has_emergency_contract: bool
    warnings: list[str]


def get_utility_businesses(db: Session, city_id: uuid.UUID) -> list[Business]:
    """Повертає всі utility-бізнеси міста (активні)."""
    return (
        db.query(Business)
        .filter(
            Business.city_id == city_id,
            Business.utility_service_type.isnot(None),
            Business.status == "active",
        )
        .all()
    )


def get_utility_businesses_by_type(db: Session, city_id: uuid.UUID, service_type: str) -> list[Business]:
    """Повертає utility-бізнеси заданого типу."""
    return [b for b in get_utility_businesses(db, city_id) if b.utility_service_type == service_type]


def get_total_capacity_by_type(db: Session, city_id: uuid.UUID, service_type: str) -> float:
    """Сумарна потужність utility-служб заданого типу."""
    businesses = get_utility_businesses_by_type(db, city_id, service_type)
    return sum(float(b.service_capacity) for b in businesses)


def process_utility_payments(db: Session, city_id: uuid.UUID, game_day: int) -> dict:
    """Щоденні комунальні платежі: бізнеси платять utility-службам.

    Кожен активний бізнес міста платить комунальний збір з cash_balance.
    Збір розподіляється між utility-службами пропорційно їхній кількості
    (для простоти Phase G3; Phase G5 прив'яже до реального споживання).

    Utility-служби платять податок (UTILITY_TAX_RATE) у казну з отриманого.
    """
    all_businesses = db.query(Business).filter(Business.city_id == city_id, Business.status == "active").all()
    utility_businesses = [b for b in all_businesses if b.utility_service_type is not None]
    non_utility = [b for b in all_businesses if b.utility_service_type is None]

    if not utility_businesses:
        return {"total_collected": Decimal("0.00"), "tax_to_treasury": Decimal("0.00")}

    total_collected = Decimal("0.00")
    total_tax = Decimal("0.00")

    # Кожен бізнес платить комунальний збір
    for business in non_utility:
        fee = UTILITY_FEE_BY_BUSINESS_TYPE.get(business.type, DEFAULT_UTILITY_FEE)
        balance = Decimal(str(business.cash_balance))
        if balance < fee:
            # Бізнес не може платити — пропускає (Phase G5: банк → кредит)
            continue
        business.cash_balance = balance - fee
        total_collected += fee

    # Розподіл між utility-службами порівну (спрощено для Phase G3)
    if utility_businesses:
        share_per_utility = total_collected / Decimal(str(len(utility_businesses)))
        for utility in utility_businesses:
            utility.cash_balance = Decimal(str(utility.cash_balance)) + share_per_utility
            # Utility платить податок у казну
            tax = share_per_utility * UTILITY_TAX_RATE
            utility.cash_balance = Decimal(str(utility.cash_balance)) - tax
            city = db.query(City).filter(City.id == city_id).first()
            if city:
                city.treasury_balance = Decimal(str(city.treasury_balance)) + tax
            total_tax += tax

    db.flush()
    logger.info(
        "Utility payments день %d: зібрано=%s, податок у казну=%s",
        game_day,
        total_collected,
        total_tax,
    )
    return {"total_collected": total_collected, "tax_to_treasury": total_tax}


def check_utility_bankruptcy(db: Session, city_id: uuid.UUID, game_day: int) -> list[dict]:
    """Перевіряє utility-служби на банкрутство і створює екстрені контракти.

    Логіка:
    1. Якщо utility-служба має cash_balance < 0 → банкрот.
    2. Якщо немає активної utility-служби данного типу → екстрений контракт.
    3. Екстрений контракт: завищена ціна, мерія платить різницю.

    Повертає список створених екстрених контрактів.
    """
    created_contracts: list[dict] = []

    for service_type in UTILITY_SERVICE_TYPES:
        businesses = get_utility_businesses_by_type(db, city_id, service_type)
        has_active = any(Decimal(str(b.cash_balance)) > 0 for b in businesses)

        if has_active:
            # Є активна служба — перевіряємо чи не банкрот
            for b in businesses:
                if Decimal(str(b.cash_balance)) < 0:
                    b.status = "bankrupt"
                    logger.warning(
                        "Utility-служба %s (тип=%s) банкрот у день %d",
                        b.name,
                        service_type,
                        game_day,
                    )
            continue

        # Немає активної служби → перевіряємо чи вже є екстрений контракт
        existing = (
            db.query(UtilityEmergencyContract)
            .filter(
                UtilityEmergencyContract.city_id == city_id,
                UtilityEmergencyContract.utility_service_type == service_type,
                UtilityEmergencyContract.is_active.is_(True),
            )
            .first()
        )
        if existing:
            continue

        # Створюємо екстрений контракт
        normal_price = NORMAL_PRICE_PER_UNIT.get(service_type, Decimal("0.50"))
        emergency_price = normal_price * EMERGENCY_PRICE_MULTIPLIER

        contract = UtilityEmergencyContract(
            city_id=city_id,
            utility_service_type=service_type,
            provider_name=f"Сусіднє місто ({service_type})",
            price_per_unit=emergency_price,
            normal_price_per_unit=normal_price,
            started_at_game_day=game_day,
            is_active=True,
        )
        db.add(contract)

        # Мерія платить різницю з казни
        price_diff = emergency_price - normal_price
        city = db.query(City).filter(City.id == city_id).first()
        if city:
            city.treasury_balance = Decimal(str(city.treasury_balance)) - price_diff

        created_contracts.append(
            {
                "service_type": service_type,
                "provider_name": contract.provider_name,
                "price_per_unit": float(emergency_price),
                "normal_price_per_unit": float(normal_price),
                "city_subsidy": float(price_diff),
            }
        )
        logger.warning(
            "Створено екстрений контракт для %s: ціна=%s (норма=%s), субсидія=%s",
            service_type,
            emergency_price,
            normal_price,
            price_diff,
        )

    db.flush()
    return created_contracts


def get_utility_status(db: Session, city_id: uuid.UUID) -> list[UtilityServiceStatus]:
    """Повертає статус всіх utility-служб міста для попереджень мера."""
    statuses: list[UtilityServiceStatus] = []

    for service_type in UTILITY_SERVICE_TYPES:
        businesses = get_utility_businesses_by_type(db, city_id, service_type)
        total_capacity = sum(float(b.service_capacity) for b in businesses)
        total_load = sum(float(b.service_load) for b in businesses)
        load_ratio = total_load / total_capacity if total_capacity > 0 else 0.0

        has_emergency = (
            db.query(UtilityEmergencyContract)
            .filter(
                UtilityEmergencyContract.city_id == city_id,
                UtilityEmergencyContract.utility_service_type == service_type,
                UtilityEmergencyContract.is_active.is_(True),
            )
            .first()
            is not None
        )

        warnings: list[str] = []
        if load_ratio > LOAD_WARNING_THRESHOLD:
            warnings.append(f"Навантаження {service_type} на {load_ratio:.0%} — близько до ліміту.")
        for b in businesses:
            if Decimal(str(b.cash_balance)) < LOW_BALANCE_WARNING:
                warnings.append(f"Служба {b.name} має низький баланс ({b.cash_balance}).")
        if not businesses:
            warnings.append(f"Немає активної служби {service_type}.")
        if has_emergency:
            warnings.append(f"Діє екстрений контракт для {service_type} — завищені ціни.")

        statuses.append(
            UtilityServiceStatus(
                service_type=service_type,
                active_businesses=len(businesses),
                total_capacity=total_capacity,
                total_load=total_load,
                load_ratio=load_ratio,
                has_emergency_contract=has_emergency,
                warnings=warnings,
            )
        )

    return statuses


def get_mayor_warnings(db: Session, city_id: uuid.UUID) -> list[str]:
    """Повертає список попереджень для мера про проблеми з utility-службами."""
    statuses = get_utility_status(db, city_id)
    warnings: list[str] = []
    for s in statuses:
        warnings.extend(s.warnings)
    return warnings


def update_service_load(db: Session, city_id: uuid.UUID, service_type: str, load: float) -> None:
    """Оновлює service_load для utility-служб заданого типу.

    Розподіляє навантаження порівну між активними службами.
    Викликається з district_metrics для реального розрахунку попиту.
    """
    businesses = get_utility_businesses_by_type(db, city_id, service_type)
    if not businesses:
        return
    load_per_business = load / len(businesses)
    for b in businesses:
        b.service_load = Decimal(str(load_per_business))
    db.flush()
