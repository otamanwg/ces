"""
Система стартапів для міського бізнесу.
Файл: backend/app/services/startup_system.py
"""

import random
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import Business, Player
from backend.app.services.ledger import credit, debit
from backend.app.services.money import money

# Етапи розвитку стартапу
STARTUP_STAGES = {
    "idea": {
        "name": "Ідея",
        "min_funding": money("0.00"),
        "max_funding": money("1000.00"),
        "success_chance": 0.60,
        "duration_days": 2,
        "next_stage_cost": money("100.00"),
        "description": "Початкова ідея бізнесу",
    },
    "prototype": {
        "name": "Прототип",
        "min_funding": money("1000.00"),
        "max_funding": money("5000.00"),
        "success_chance": 0.75,
        "duration_days": 5,
        "next_stage_cost": money("1000.00"),
        "description": "Створення прототипу продукту",
    },
    "mvp": {
        "name": "MVP",
        "min_funding": money("5000.00"),
        "max_funding": money("20000.00"),
        "success_chance": 0.85,
        "duration_days": 10,
        "next_stage_cost": money("5000.00"),
        "description": "Мінімально життєздатний продукт",
    },
    "growth": {
        "name": "Зростання",
        "min_funding": money("20000.00"),
        "max_funding": money("100000.00"),
        "success_chance": 0.95,
        "duration_days": 20,
        "next_stage_cost": None,
        "description": "Масштабування бізнесу",
    },
}


# Типи стартапів з унікальними характеристиками
STARTUP_TYPES = {
    "tech": {
        "name": "Технологічний стартап",
        "base_success_modifier": 1.1,
        "funding_multiplier": 1.5,
        "risk_level": "high",
        "market_potential": "very_high",
    },
    "retail": {
        "name": "Роздрібна торгівля",
        "base_success_modifier": 0.9,
        "funding_multiplier": 1.0,
        "risk_level": "medium",
        "market_potential": "medium",
    },
    "service": {
        "name": "Сфера послуг",
        "base_success_modifier": 1.0,
        "funding_multiplier": 0.8,
        "risk_level": "low",
        "market_potential": "medium",
    },
    "manufacturing": {
        "name": "Виробництво",
        "base_success_modifier": 0.8,
        "funding_multiplier": 2.0,
        "risk_level": "high",
        "market_potential": "high",
    },
    "food_beverage": {
        "name": "Харчова промисловість",
        "base_success_modifier": 1.0,
        "funding_multiplier": 1.2,
        "risk_level": "medium",
        "market_potential": "high",
    },
}


def create_startup(
    db: Session, player_id: str, business_type: str, idea_name: str, startup_type: str = "service"
) -> dict[str, Any]:
    """
    Створює новий стартап для гравця.
    """
    player_uuid = uuid.UUID(player_id) if isinstance(player_id, str) else player_id

    # Валідація типу стартапу
    if startup_type not in STARTUP_TYPES:
        return {"success": False, "message": "Невідомий тип стартапу"}

    # Створення бізнесу зі статусом стартапу
    startup = Business(
        name=idea_name,
        type=business_type,
        owner_player_id=player_uuid,
        is_startup=True,
        startup_stage="idea",
        business_size=1,
        cash_balance=money("100.00"),  # стартовий капітал
        management_mode="manual",
        startup_success_chance=Decimal(str(STARTUP_STAGES["idea"]["success_chance"])),
    )

    db.add(startup)
    db.commit()
    db.refresh(startup)

    return {
        "success": True,
        "message": f"Стартап '{idea_name}' створено!",
        "data": {
            "startup_id": str(startup.id),
            "stage": startup.startup_stage,
            "success_chance": float(startup.startup_success_chance),
            "startup_type": startup_type,
        },
    }


def invest_in_startup(db: Session, investor_id: str, startup_id: str, amount: float) -> dict[str, Any]:
    """
    Інвестування в стартап.
    """
    investor_uuid = uuid.UUID(investor_id) if isinstance(investor_id, str) else investor_id
    startup_uuid = uuid.UUID(startup_id) if isinstance(startup_id, str) else startup_id

    # Отримання інвестора та стартапу
    investor = db.query(Player).filter(Player.id == investor_uuid).first()
    startup = db.query(Business).filter(Business.id == startup_uuid).first()

    if not investor:
        return {"success": False, "message": "Інвестора не знайдено"}

    if not startup:
        return {"success": False, "message": "Стартап не знайдено"}

    if not startup.is_startup:
        return {"success": False, "message": "Це не стартап"}

    investment_amount = money(amount)

    if investor.balance < investment_amount:
        return {"success": False, "message": "Недостатньо коштів для інвестиції"}

    # Перевірка ліміту фінансування для етапу
    stage_config = STARTUP_STAGES[startup.startup_stage]
    current_funding = money(startup.startup_funding)
    if current_funding + investment_amount > stage_config["max_funding"]:
        return {"success": False, "message": f"Перевищено ліміть фінансування для етапу {stage_config['name']}"}

    # Виконання інвестиції
    debit(db, investor, "balance", investment_amount)
    credit(db, startup, "cash_balance", investment_amount)

    # Оновлення інформації про інвесторів
    if not startup.startup_investors:
        startup.startup_investors = {}

    startup.startup_investors[str(investor_uuid)] = float(investment_amount)
    startup.startup_funding = current_funding + investment_amount

    # Оновлення шансу успіху
    base_chance = STARTUP_STAGES[startup.startup_stage]["success_chance"]
    funding_bonus = min(0.20, float(startup.startup_funding) / float(stage_config["max_funding"]) * 0.20)
    startup.startup_success_chance = Decimal(str(base_chance + funding_bonus))

    db.commit()

    return {
        "success": True,
        "message": f"Інвестовано {investment_amount}₴ в стартап '{startup.name}'",
        "data": {
            "investment_amount": float(investment_amount),
            "total_funding": float(startup.startup_funding),
            "new_success_chance": float(startup.startup_success_chance),
            "stage": startup.startup_stage,
        },
    }


def advance_startup_stage(db: Session, startup_id: str) -> dict[str, Any]:
    """
    Переведення стартапу на наступний етап.
    """
    startup_uuid = uuid.UUID(startup_id) if isinstance(startup_id, str) else startup_id
    startup = db.query(Business).filter(Business.id == startup_uuid).first()

    if not startup:
        return {"success": False, "message": "Стартап не знайдено"}

    if not startup.is_startup:
        return {"success": False, "message": "Це не стартап"}

    current_stage = startup.startup_stage
    stage_config = STARTUP_STAGES[current_stage]

    # Перевірка достатності фінансування
    if startup.startup_funding < stage_config["min_funding"]:
        return {"success": False, "message": f"Недостатньо фінансування для етапу {stage_config['name']}"}

    # Симуляція успіху/провалу
    success_chance = float(startup.startup_success_chance)

    if random.random() > success_chance:
        # Стартап провалився
        startup.status = "bankrupt"
        startup.is_startup = False
        db.commit()

        return {
            "success": False,
            "message": f"Стартап '{startup.name}' провалився на етапі {stage_config['name']}!",
            "data": {"failed_stage": current_stage, "total_funding_lost": float(startup.startup_funding)},
        }

    # Успішне просування на наступний етап
    stage_order = ["idea", "prototype", "mvp", "growth"]
    current_index = stage_order.index(current_stage)

    if current_index >= len(stage_order) - 1:
        # Стартап успішно завершив всі етапи
        startup.is_startup = False
        startup.business_size = 10  # починаємо з малого бізнесу
        startup.management_mode = "manual"  # даємо вибір гравцю

        db.commit()

        return {
            "success": True,
            "message": f"Вітаємо! Стартап '{startup.name}' успішно завершив усі етапи!",
            "data": {
                "final_stage": current_stage,
                "business_size": startup.business_size,
                "total_investment": float(startup.startup_funding),
            },
        }

    # Перехід на наступний етап
    next_stage = stage_order[current_index + 1]
    next_config = STARTUP_STAGES[next_stage]

    startup.startup_stage = next_stage
    startup.startup_success_chance = Decimal(str(next_config["success_chance"]))

    # Витрата на перехід
    if stage_config["next_stage_cost"]:
        debit(db, startup, "cash_balance", stage_config["next_stage_cost"])

    db.commit()

    return {
        "success": True,
        "message": f"Стартап '{startup.name}' перейшов на етап {next_config['name']}!",
        "data": {
            "previous_stage": current_stage,
            "new_stage": next_stage,
            "new_success_chance": float(startup.startup_success_chance),
            "next_stage_cost": float(next_config["next_stage_cost"]) if next_config["next_stage_cost"] else None,
        },
    }


def get_startup_info(db: Session, startup_id: str) -> dict[str, Any]:
    """
    Отримання детальної інформації про стартап.
    """
    startup_uuid = uuid.UUID(startup_id) if isinstance(startup_id, str) else startup_id
    startup = db.query(Business).filter(Business.id == startup_uuid).first()

    if not startup:
        return {"success": False, "message": "Стартап не знайдено"}

    stage_config = STARTUP_STAGES[startup.startup_stage]

    return {
        "success": True,
        "data": {
            "id": str(startup.id),
            "name": startup.name,
            "type": startup.type,
            "stage": startup.startup_stage,
            "stage_name": stage_config["name"],
            "stage_description": stage_config["description"],
            "funding": float(startup.startup_funding),
            "min_funding": float(stage_config["min_funding"]),
            "max_funding": float(stage_config["max_funding"]),
            "success_chance": float(startup.startup_success_chance),
            "cash_balance": float(startup.cash_balance),
            "investors": startup.startup_investors or {},
            "duration_days": stage_config["duration_days"],
            "next_stage_cost": float(stage_config["next_stage_cost"]) if stage_config["next_stage_cost"] else None,
        },
    }


def list_available_startups(db: Session, city_id: str = None, stage: str = None) -> dict[str, Any]:
    """
    Список доступних для інвестування стартапів.
    """
    query = db.query(Business).filter(Business.is_startup, Business.status == "active")

    if city_id:
        city_uuid = uuid.UUID(city_id) if isinstance(city_id, str) else city_id
        query = query.filter(Business.city_id == city_uuid)

    if stage:
        query = query.filter(Business.startup_stage == stage)

    startups = query.all()

    result = []
    for startup in startups:
        stage_config = STARTUP_STAGES[startup.startup_stage]

        result.append(
            {
                "id": str(startup.id),
                "name": startup.name,
                "type": startup.type,
                "stage": startup.startup_stage,
                "stage_name": stage_config["name"],
                "funding": float(startup.startup_funding),
                "max_funding": float(stage_config["max_funding"]),
                "success_chance": float(startup.startup_success_chance),
                "funding_progress": float(startup.startup_funding) / float(stage_config["max_funding"]) * 100,
                "owner_id": str(startup.owner_player_id) if startup.owner_player_id else None,
            }
        )

    return {"success": True, "data": {"startups": result, "total_count": len(result)}}


def calculate_startup_roi(startup: Business) -> float:
    """
    Розрахунок потенційного ROI для інвесторів.
    """
    if not startup.is_startup:
        return 0.0

    stage_config = STARTUP_STAGES[startup.startup_stage]

    # Базовий ROI залежно від етапу
    base_roi = {
        "idea": 10.0,  # 10x потенційний дохід
        "prototype": 5.0,  # 5x
        "mvp": 3.0,  # 3x
        "growth": 1.5,  # 1.5x
    }

    roi = base_roi.get(startup.startup_stage, 1.0)

    # Модифікатор успішності
    success_modifier = float(startup.startup_success_chance) / stage_config["success_chance"]

    return roi * success_modifier
