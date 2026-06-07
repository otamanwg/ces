"""
API ендпоінти для управління бізнесом.
Файл: backend/app/api/routes/business_management.py
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Business, Player
from backend.app.schemas.response import api_success
from backend.app.services.auth import get_authorized_player
from backend.app.services.business_management import (
    get_business_tier,
    process_manual_management,
    process_shadow_operations,
    switch_management_mode,
    update_business_size,
)
from backend.app.services.daily_business_revenue import process_daily_business_revenue

router = APIRouter(prefix="/business", tags=["business"])


def require_player(db: Session, player_id: str, player_token: str | None) -> Player | None:
    return get_authorized_player(db, player_id, player_token)


@router.post("/{business_id}/switch-mode")
async def switch_business_mode(
    business_id: str,
    new_mode: str,
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Перемикає режим управління бізнесом (ai/manual/shadow).
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business).filter(Business.id == UUID(business_id), Business.owner_player_id == player.id).first()
    )

    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено або ви не є власником")

    result = switch_management_mode(db, business, new_mode, str(player.id))

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.post("/{business_id}/update-size")
async def update_business_size_endpoint(
    business_id: str,
    new_size: int,
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Оновлює розмір бізнесу (кількість працівників).
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business).filter(Business.id == UUID(business_id), Business.owner_player_id == player.id).first()
    )

    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено або ви не є власником")

    if new_size < 1 or new_size > 10000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний розмір бізнесу (1-10000)")

    result = update_business_size(db, business, new_size)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.post("/{business_id}/manual-operation")
async def manual_business_operation(
    business_id: str,
    decision: str = "standard",
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Виконує ручну операцію бізнесу з вибором стратегії.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business)
        .filter(
            Business.id == UUID(business_id),
            Business.owner_player_id == player.id,
            Business.management_mode == "manual",
        )
        .first()
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено, не ваш, або не в ручному режимі"
        )

    if decision not in ["standard", "aggressive", "conservative", "innovation"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректне рішення")

    result = process_manual_management(db, business, decision)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.post("/{business_id}/shadow-operation")
async def shadow_business_operation(
    business_id: str,
    operation_type: str = "standard",
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Виконує тіньову операцію бізнесу.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business)
        .filter(
            Business.id == UUID(business_id),
            Business.owner_player_id == player.id,
            Business.management_mode == "shadow",
        )
        .first()
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено, не ваш, або не в тіньовому режимі"
        )

    if operation_type not in ["standard", "aggressive", "illegal"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний тип операції")

    result = process_shadow_operations(db, business, operation_type)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.get("/{business_id}/status")
async def get_business_status(
    business_id: str,
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує детальний статус бізнесу.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business).filter(Business.id == UUID(business_id), Business.owner_player_id == player.id).first()
    )

    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено або ви не є власником")

    tier = get_business_tier(business.business_size)

    return api_success(
        message="Статус бізнесу",
        data={
            "id": str(business.id),
            "name": business.name,
            "type": business.type,
            "status": business.status,
            "management_mode": business.management_mode,
            "business_size": business.business_size,
            "tier": tier,
            "cash_balance": float(business.cash_balance),
            "daily_revenue": float(business.daily_revenue),
            "ai_profit_rate": float(business.ai_profit_rate) if business.ai_profit_rate else None,
            "is_startup": business.is_startup,
            "startup_stage": business.startup_stage if business.is_startup else None,
            "startup_funding": float(business.startup_funding) if business.is_startup else None,
            "startup_success_chance": float(business.startup_success_chance) if business.is_startup else None,
            "profit_margin": float(business.profit_margin),
            "market_share": float(business.market_share),
        },
    )


@router.post("/{business_id}/collect-revenue")
async def collect_daily_revenue(
    business_id: str,
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Збирає щоденний дохід бізнесу (вручну).
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    business = (
        db.query(Business)
        .filter(Business.id == UUID(business_id), Business.owner_player_id == player.id, Business.status == "active")
        .first()
    )

    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бізнес не знайдено, не ваш, або не активний")

    result = process_daily_business_revenue(db, business)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.get("/my-businesses")
async def get_my_businesses(
    player_id: str,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує список всіх бізнесів гравця.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    businesses = db.query(Business).filter(Business.owner_player_id == player.id).all()

    result = []
    for business in businesses:
        tier = get_business_tier(business.business_size)

        result.append(
            {
                "id": str(business.id),
                "name": business.name,
                "type": business.type,
                "status": business.status,
                "management_mode": business.management_mode,
                "business_size": business.business_size,
                "tier": tier,
                "cash_balance": float(business.cash_balance),
                "daily_revenue": float(business.daily_revenue),
                "is_startup": business.is_startup,
                "startup_stage": business.startup_stage if business.is_startup else None,
            }
        )

    return api_success(message="Список ваших бізнесів", data={"businesses": result, "total_count": len(result)})


@router.get("/tiers")
async def get_business_tiers():
    """
    Отримує інформацію про рівні бізнесу.
    """
    from backend.app.services.business_management import BUSINESS_SIZE_TIERS

    return api_success(message="Рівні бізнесу", data=BUSINESS_SIZE_TIERS)
