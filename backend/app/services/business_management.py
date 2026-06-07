"""
Система управління бізнесом з прогресивною шкалою доходності.
Файл: backend/app/services/business_management.py
"""

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import Business
from backend.app.services.ledger import credit, debit
from backend.app.services.money import money

# Прогресивні таблиці для AI управління
BUSINESS_SIZE_TIERS = {
    "micro": {
        "max_employees": 5,
        "ai_profit_rate": 0.15,  # 15%
        "tax_rate": 0.05,  # 5%
        "base_revenue": money("200.00"),
        "management_fee": 0.05,  # 5% від доходу
    },
    "small": {
        "max_employees": 50,
        "ai_profit_rate": 0.10,  # 10%
        "tax_rate": 0.10,  # 10%
        "base_revenue": money("1000.00"),
        "management_fee": 0.05,  # 5% від доходу
    },
    "medium": {
        "max_employees": 200,
        "ai_profit_rate": 0.07,  # 7%
        "tax_rate": 0.15,  # 15%
        "base_revenue": money("5000.00"),
        "management_fee": 0.04,  # 4% від доходу
    },
    "large": {
        "max_employees": 1000,
        "ai_profit_rate": 0.05,  # 5%
        "tax_rate": 0.20,  # 20%
        "base_revenue": money("15000.00"),
        "management_fee": 0.03,  # 3% від доходу
    },
    "mega": {
        "max_employees": 9999,
        "ai_profit_rate": 0.04,  # 4%
        "tax_rate": 0.25,  # 25%
        "base_revenue": money("50000.00"),
        "management_fee": 0.02,  # 2% від доходу
    },
}


def get_business_tier(business_size: int) -> str:
    """Визначає рівень бізнесу за кількістю працівників."""
    if business_size <= 5:
        return "micro"
    elif business_size <= 50:
        return "small"
    elif business_size <= 200:
        return "medium"
    elif business_size <= 1000:
        return "large"
    else:
        return "mega"


def calculate_ai_profit_rate(business: Business) -> Decimal:
    """
    Розраховує динамічний % прибутку для AI управління.
    Чим більший бізнес - тим нижчий % прибутку.
    """
    tier = get_business_tier(business.business_size)
    return Decimal(str(BUSINESS_SIZE_TIERS[tier]["ai_profit_rate"]))


def calculate_business_daily_revenue(business: Business) -> Decimal:
    """
    Розраховує щоденний дохід бізнесу залежно від типу та розміру.
    """
    tier = get_business_tier(business.business_size)
    base_revenue = BUSINESS_SIZE_TIERS[tier]["base_revenue"]

    # Модифікатори залежно від типу бізнесу
    type_modifiers = {
        "shop": 1.0,
        "factory": 2.5,
        "utility_water": 1.2,
        "utility_housing": 1.5,
        "private_hostel": 1.3,
        "restaurant": 1.8,
        "cafe": 0.8,
        "fitness": 1.1,
        "beauty": 0.7,
        "tech": 3.0,
        "logistics": 2.0,
    }

    modifier = type_modifiers.get(business.type, 1.0)
    return money(base_revenue * Decimal(str(modifier)))


def process_ai_management(db: Session, business: Business) -> dict[str, Any]:
    """
    Обробляє щоденне AI управління бізнесом.
    """
    if business.management_mode != "ai":
        return {"success": False, "message": "Бізнес не в AI режимі"}

    tier = get_business_tier(business.business_size)
    tier_config = BUSINESS_SIZE_TIERS[tier]

    # Розрахунок доходу
    daily_revenue = calculate_business_daily_revenue(business)
    ai_profit = daily_revenue * Decimal(str(tier_config["ai_profit_rate"]))

    # Розрахунок податків
    taxes = ai_profit * Decimal(str(tier_config["tax_rate"]))

    # Плата за управління
    management_fee = ai_profit * Decimal(str(tier_config["management_fee"]))

    # Чистий дохід
    net_profit = ai_profit - taxes - management_fee

    # Виконання транзакцій - додаємо прибуток на рахунок бізнесу
    credit(db, business, "cash_balance", net_profit)

    # Оновлення показників
    business.daily_revenue = daily_revenue
    business.ai_profit_rate = calculate_ai_profit_rate(business)

    return {
        "success": True,
        "data": {
            "daily_revenue": float(daily_revenue),
            "ai_profit": float(ai_profit),
            "taxes": float(taxes),
            "management_fee": float(management_fee),
            "net_profit": float(net_profit),
            "tier": tier,
        },
    }


def process_manual_management(db: Session, business: Business, player_decision: str = "standard") -> dict[str, Any]:
    """
    Обробляє ручне управління бізнесом з вибором гравця.
    """
    if business.management_mode != "manual":
        return {"success": False, "message": "Бізнес не в ручному режимі"}

    base_revenue = calculate_business_daily_revenue(business)

    # Вибори гравця впливають на дохід та ризик
    decisions = {
        "standard": {"revenue_modifier": 1.0, "risk": 0.05},
        "aggressive": {"revenue_modifier": 1.5, "risk": 0.15},
        "conservative": {"revenue_modifier": 0.8, "risk": 0.02},
        "innovation": {"revenue_modifier": 2.0, "risk": 0.25},
    }

    decision = decisions.get(player_decision, decisions["standard"])
    actual_revenue = base_revenue * Decimal(str(decision["revenue_modifier"]))

    # Симуляція ризику
    import random

    if random.random() < decision["risk"]:
        # Щось пішло не так
        actual_revenue = actual_revenue * Decimal("0.5")
        success = False
        message = "Щось пішло не так! Дохід зменшено вдвічі."
    else:
        success = True
        message = "Робочий день пройшов успішно!"

    # Стандартні податки
    tier = get_business_tier(business.business_size)
    tax_rate = Decimal(str(BUSINESS_SIZE_TIERS[tier]["tax_rate"]))
    taxes = actual_revenue * tax_rate

    # Чистий дохід
    net_profit = actual_revenue - taxes

    # Виконання транзакцій
    credit(db, business, "cash_balance", net_profit)
    business.daily_revenue = actual_revenue

    return {
        "success": success,
        "message": message,
        "data": {
            "daily_revenue": float(actual_revenue),
            "taxes": float(taxes),
            "net_profit": float(net_profit),
            "decision": player_decision,
        },
    }


def process_shadow_operations(db: Session, business: Business, operation_type: str = "standard") -> dict[str, Any]:
    """
    Обробляє тіньові операції бізнесу з високим ризиком та доходом.
    """
    if business.management_mode != "shadow":
        return {"success": False, "message": "Бізнес не в тіньовому режимі"}

    base_revenue = calculate_business_daily_revenue(business)

    # Тіньові операції дають вищий дохід але з високим ризиком
    shadow_operations = {
        "standard": {"revenue_modifier": 3.0, "risk": 0.20, "legal_risk": 0.10},
        "aggressive": {"revenue_modifier": 5.0, "risk": 0.35, "legal_risk": 0.25},
        "illegal": {"revenue_modifier": 10.0, "risk": 0.50, "legal_risk": 0.40},
    }

    operation = shadow_operations.get(operation_type, shadow_operations["standard"])
    potential_revenue = base_revenue * Decimal(str(operation["revenue_modifier"]))

    import random

    # Перевірка ризику провалу операції
    if random.random() < operation["risk"]:
        # Операція провалилась
        loss = base_revenue * Decimal("0.5")
        debit(db, business, "cash_balance", loss)
        return {
            "success": False,
            "message": "Тіньова операція провалилась! Ви втратили гроші.",
            "data": {"loss": float(loss)},
        }

    # Перевірка юридичного ризику
    if random.random() < operation["legal_risk"]:
        # Поліція виявила порушення
        fine = potential_revenue * Decimal("0.3")
        debit(db, business, "cash_balance", fine)
        return {
            "success": False,
            "message": "Поліція виявила порушення! Штраф накладено.",
            "data": {"fine": float(fine)},
        }

    # Успішна тіньова операція
    net_profit = potential_revenue  # тіньові операції не оподатковуються

    # Виконання транзакцій
    credit(db, business, "cash_balance", net_profit)
    business.daily_revenue = potential_revenue

    return {
        "success": True,
        "message": "Тіньова операція пройшла успішно!",
        "data": {
            "daily_revenue": float(potential_revenue),
            "net_profit": float(net_profit),
            "operation": operation_type,
        },
    }


def switch_management_mode(db: Session, business: Business, new_mode: str, player_id: str = None) -> dict[str, Any]:
    """
    Перемикає режим управління бізнесом.
    """
    if new_mode not in ["ai", "manual", "shadow"]:
        return {"success": False, "message": "Невідомий режим управління"}

    old_mode = business.management_mode

    # Перевірка умов переходу
    if new_mode == "shadow" and old_mode != "shadow":
        # Для переходу в тіньовий режим потрібна певна репутація
        # TODO: перевірити репутацію гравця
        pass

    # Зміна режиму
    business.management_mode = new_mode

    # Оновлення AI profit rate якщо потрібно
    if new_mode == "ai":
        business.ai_profit_rate = calculate_ai_profit_rate(business)

    return {
        "success": True,
        "message": f"Режим управління змінено з {old_mode} на {new_mode}",
        "data": {
            "old_mode": old_mode,
            "new_mode": new_mode,
            "ai_profit_rate": float(business.ai_profit_rate) if new_mode == "ai" else None,
        },
    }


def update_business_size(db: Session, business: Business, new_size: int) -> dict[str, Any]:
    """
    Оновлює розмір бізнесу та перераховує AI profit rate.
    """
    old_size = business.business_size
    old_tier = get_business_tier(old_size)
    new_tier = get_business_tier(new_size)

    business.business_size = new_size

    # Оновлення AI profit rate якщо в AI режимі
    if business.management_mode == "ai":
        business.ai_profit_rate = calculate_ai_profit_rate(business)

    return {
        "success": True,
        "message": f"Розмір бізнесу змінено з {old_size} на {new_size} працівників",
        "data": {
            "old_size": old_size,
            "new_size": new_size,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "ai_profit_rate": float(business.ai_profit_rate) if business.management_mode == "ai" else None,
        },
    }
