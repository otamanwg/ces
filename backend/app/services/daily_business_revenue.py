"""
Щоденна генерація доходів бізнесу - вирішує проблему відсутності доходів.
Файл: backend/app/services/daily_business_revenue.py
"""

import random
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import Business, City
from backend.app.services.business_management import (
    get_business_tier,
    process_ai_management,
    process_manual_management,
    process_shadow_operations,
)
from backend.app.services.ledger import credit
from backend.app.services.money import money

# Базові налаштування генерації доходів
BUSINESS_REVENUE_CONFIG = {
    "shop": {
        "base_daily_revenue": 300,
        "customer_range": (20, 50),
        "avg_transaction": 15,
        "market_saturation_factor": 0.8,
    },
    "factory": {
        "base_daily_revenue": 2000,
        "production_units": (100, 300),
        "unit_price": 25,
        "market_demand_factor": 0.9,
    },
    "utility_water": {
        "base_daily_revenue": 800,
        "subscribers": (200, 500),
        "avg_monthly_bill": 50,
        "essential_service": True,
    },
    "utility_housing": {
        "base_daily_revenue": 1200,
        "tenants": (50, 150),
        "avg_monthly_rent": 80,
        "essential_service": True,
    },
    "private_hostel": {"base_daily_revenue": 200, "beds": (20, 50), "occupancy_rate": 0.75, "daily_rate": 15},
    "restaurant": {"base_daily_revenue": 600, "customers": (30, 80), "avg_check": 25, "seasonal_factor": 1.2},
    "cafe": {"base_daily_revenue": 250, "customers": (40, 100), "avg_check": 8, "peak_hours_bonus": 1.3},
    "fitness": {"base_daily_revenue": 400, "members": (80, 200), "monthly_fee": 30, "retention_rate": 0.85},
    "beauty": {"base_daily_revenue": 350, "clients": (15, 40), "avg_service_price": 45, "appointment_rate": 0.7},
    "tech": {"base_daily_revenue": 1500, "projects": (2, 8), "avg_project_value": 500, "innovation_bonus": 1.5},
    "logistics": {
        "base_daily_revenue": 1000,
        "deliveries": (50, 150),
        "avg_delivery_fee": 12,
        "fuel_cost_factor": 0.15,
    },
}


def calculate_business_expenses(business: Business) -> Decimal:
    """
    Розрахунок щоденних витрат бізнесу.
    """
    tier = get_business_tier(business.business_size)

    # Базові витрати залежно від розміру
    base_expenses = {
        "micro": money("50.00"),
        "small": money("200.00"),
        "medium": money("800.00"),
        "large": money("3000.00"),
        "mega": money("10000.00"),
    }

    expenses = base_expenses[tier]

    # Галузеві модифікатори витрат
    industry_multipliers = {
        "factory": 1.5,  # висока вартість сировини
        "tech": 0.8,  # низькі операційні витрати
        "restaurant": 1.3,  # витрати на продукти
        "retail": 1.1,  # оренда + персонал
        "service": 0.9,  # помірні витрати
    }

    # Визначення категорії бізнесу
    if business.type in ["factory"]:
        category = "factory"
    elif business.type in ["tech"]:
        category = "tech"
    elif business.type in ["restaurant"]:
        category = "restaurant"
    elif business.type in ["shop"]:
        category = "retail"
    else:
        category = "service"

    expenses = expenses * Decimal(str(industry_multipliers.get(category, 1.0)))

    return expenses


def _competition_modifier_from_count(count: int) -> float:
    if count == 0:
        return 1.2
    elif count <= 2:
        return 1.0
    elif count <= 5:
        return 0.8
    else:
        return 0.6


def calculate_market_competition_modifier(
    db: Session, business: Business, competition_cache: dict[str, int] | None = None
) -> float:
    """
    Розрахунок модифікатора через конкуренцію в місті.
    Якщо переданий competition_cache — використовує його замість DB запиту.
    """
    if competition_cache is not None:
        total = competition_cache.get(business.type, 0)
        similar_businesses = max(0, total - 1)  # виключаємо сам бізнес
    else:
        similar_businesses = (
            db.query(Business)
            .filter(
                Business.city_id == business.city_id,
                Business.type == business.type,
                Business.status == "active",
                Business.id != business.id,
            )
            .count()
        )
    return _competition_modifier_from_count(similar_businesses)


def calculate_location_modifier(business: Business, city_metrics: dict = None) -> float:
    """
    Модифікатор залежно від локації та престижу району.
    """
    # Базові модифікатори (поки фіксовані, потім будуть динамічними)

    # Для простоти використовуємо середній модифікатор
    # TODO: інтегрувати з DistrictPrestige коли буде готова
    return 1.0


def process_daily_business_revenue(
    db: Session, business: Business, competition_cache: dict[str, int] | None = None
) -> dict[str, Any]:
    """
    Основна функція - обробляє щоденний дохід бізнесу залежно від режиму управління.
    Бізнеси без явного management_mode або з business_size == 0 пропускаються.
    """
    if business.status != "active":
        return {"success": False, "message": "Бізнес не активний"}

    if not business.management_mode or business.business_size == 0:
        return {"success": False, "message": "Режим управління не встановлено"}

    # Обробка залежно від режиму управління
    if business.management_mode == "ai":
        return process_ai_management(db, business)
    elif business.management_mode == "manual":
        return process_manual_management(db, business, "standard")
    elif business.management_mode == "shadow":
        return process_shadow_operations(db, business, "standard")
    else:
        return generate_base_revenue(db, business, competition_cache=competition_cache)


def generate_base_revenue(
    db: Session, business: Business, competition_cache: dict[str, int] | None = None
) -> dict[str, Any]:
    """
    Генерація базового доходу для бізнесу без спеціального управління.
    """
    config = BUSINESS_REVENUE_CONFIG.get(business.type, BUSINESS_REVENUE_CONFIG["shop"])

    # Базовий дохід
    base_revenue = money(config["base_daily_revenue"])

    # Модифікатор розміру бізнесу
    size_modifier = 1.0 + (business.business_size - 1) * 0.1  # +10% за кожного працівника

    # Ринкові модифікатори
    competition_modifier = calculate_market_competition_modifier(db, business, competition_cache)
    location_modifier = calculate_location_modifier(business)

    # Випадковий фактор (80-120% від базового)
    random_factor = random.uniform(0.8, 1.2)

    # Розрахунок фінального доходу
    gross_revenue = base_revenue * Decimal(
        str(size_modifier * competition_modifier * location_modifier * random_factor)
    )

    # Витрати
    expenses = calculate_business_expenses(business)

    # Податки (10% базові)
    taxes = gross_revenue * Decimal("0.10")

    # Чистий дохід
    net_profit = gross_revenue - expenses - taxes

    # Перевірка на банкрутство
    if Decimal(str(business.cash_balance)) + net_profit < money("-5000.00"):
        business.status = "bankrupt"
        db.commit()
        return {
            "success": False,
            "message": f"Бізнес '{business.name}' збанкрутував!",
            "data": {"final_balance": float(business.cash_balance)},
        }

    # Виконання транзакцій
    credit(db, business, "cash_balance", net_profit)

    # Оновлення показників
    business.daily_revenue = gross_revenue

    db.commit()

    return {
        "success": True,
        "message": f"Бізнес '{business.name}' заробив {net_profit}₴",
        "data": {
            "gross_revenue": float(gross_revenue),
            "expenses": float(expenses),
            "taxes": float(taxes),
            "net_profit": float(net_profit),
            "size_modifier": size_modifier,
            "competition_modifier": competition_modifier,
            "random_factor": random_factor,
        },
    }


def process_all_businesses_daily_revenue(db: Session, city_id: str = None) -> dict[str, Any]:
    """
    Обробляє щоденні доходи всіх активних бізнесів у місті.
    """
    query = db.query(Business).filter(
        Business.status == "active",
        Business.management_mode == "ai",
        Business.business_size > 0,
    )

    if city_id:
        query = query.filter(Business.city_id == city_id)

    businesses = query.all()

    # Одним запитом обчислюємо кількість активних бізнесів по типах у місті
    competition_filter = [Business.status == "active"]
    if city_id:
        competition_filter.append(Business.city_id == city_id)
    competition_cache: dict[str, int] = {
        row[0]: row[1]
        for row in db.query(Business.type, func.count(Business.id))
        .filter(*competition_filter)
        .group_by(Business.type)
        .all()
    }

    results = {
        "total_businesses": len(businesses),
        "successful": 0,
        "failed": 0,
        "total_revenue": 0.0,
        "total_expenses": 0.0,
        "total_taxes": 0.0,
        "bankrupted": 0,
        "details": [],
    }

    for business in businesses:
        try:
            result = process_daily_business_revenue(db, business, competition_cache=competition_cache)

            if result["success"]:
                results["successful"] += 1
                data = result.get("data", {})
                results["total_revenue"] += data.get("gross_revenue", 0)
                results["total_expenses"] += data.get("expenses", 0)
                results["total_taxes"] += data.get("taxes", 0)
            else:
                results["failed"] += 1
                if "збанкрутував" in result.get("message", ""):
                    results["bankrupted"] += 1

            results["details"].append(
                {
                    "business_id": str(business.id),
                    "business_name": business.name,
                    "business_type": business.type,
                    "management_mode": business.management_mode,
                    "success": result["success"],
                    "message": result.get("message", ""),
                    "net_profit": result.get("data", {}).get("net_profit", 0),
                }
            )

        except Exception as e:
            results["failed"] += 1
            results["details"].append(
                {
                    "business_id": str(business.id),
                    "business_name": business.name,
                    "success": False,
                    "message": f"Помилка обробки: {str(e)}",
                    "net_profit": 0,
                }
            )

    return {"success": True, "message": f"Оброблено {results['total_businesses']} бізнесів", "data": results}


def simulate_economic_cycle(db: Session, city_id: str, days: int = 30) -> dict[str, Any]:
    """
    Симуляція економічного циклу для тестування балансу.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    daily_results = []

    for day in range(days):
        # Обробка доходів всіх бізнесів
        result = process_all_businesses_daily_revenue(db, city_id)

        # Оновлення міських метрик (спрощено)
        if result["success"]:
            data = result["data"]
            # TODO: інтегрувати з CityMetrics коли буде готова

        daily_results.append(
            {
                "day": day + 1,
                "total_revenue": data.get("total_revenue", 0),
                "total_expenses": data.get("total_expenses", 0),
                "total_taxes": data.get("total_taxes", 0),
                "successful_businesses": data.get("successful", 0),
                "failed_businesses": data.get("failed", 0),
                "bankrupted_today": data.get("bankrupted", 0),
            }
        )

    # Підсумки симуляції
    total_revenue = sum(day["total_revenue"] for day in daily_results)
    total_expenses = sum(day["total_expenses"] for day in daily_results)
    total_taxes = sum(day["total_taxes"] for day in daily_results)
    total_bankrupted = sum(day["bankrupted_today"] for day in daily_results)

    return {
        "success": True,
        "message": f"Симуляція {days}-денного циклу завершена",
        "data": {
            "city_id": city_id,
            "simulated_days": days,
            "daily_results": daily_results,
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "total_taxes": total_taxes,
                "net_profit": total_revenue - total_expenses - total_taxes,
                "total_bankrupted": total_bankrupted,
                "average_daily_revenue": total_revenue / days,
                "economic_stability": "stable" if total_bankrupted < 3 else "unstable",
            },
        },
    }
