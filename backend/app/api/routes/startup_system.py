"""
API ендпоінти для системи стартапів.
Файл: backend/app/api/routes/startup_system.py
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Business, Player
from backend.app.schemas.response import api_success
from backend.app.services.auth import get_authorized_player
from backend.app.services.startup_system import (
    STARTUP_STAGES,
    STARTUP_TYPES,
    advance_startup_stage,
    calculate_startup_roi,
    create_startup,
    get_startup_info,
    invest_in_startup,
    list_available_startups,
)

router = APIRouter(prefix="/startup", tags=["startup"])


def require_player(db: Session, player_id: str, player_token: str | None) -> Player | None:
    return get_authorized_player(db, player_id, player_token)


@router.post("/create")
async def create_new_startup(
    business_type: str,
    idea_name: str,
    startup_type: str = "service",
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Створює новий стартап.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    result = create_startup(db, str(player.id), business_type, idea_name, startup_type)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.post("/{startup_id}/invest")
async def invest_in_startup_endpoint(
    startup_id: str,
    amount: float,
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Інвестує в стартап.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сума інвестиції повинна бути позитивною")

    result = invest_in_startup(db, str(player.id), startup_id, amount)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.post("/{startup_id}/advance-stage")
async def advance_startup_stage_endpoint(
    startup_id: str,
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Переводить стартап на наступний етап.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    # Перевіряємо чи гравець є власником стартапу
    startup = (
        db.query(Business)
        .filter(Business.id == UUID(startup_id), Business.owner_player_id == player.id, Business.is_startup)
        .first()
    )

    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Стартап не знайдено або ви не є власником")

    result = advance_startup_stage(db, startup_id)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return api_success(message=result["message"], data=result["data"])


@router.get("/{startup_id}")
async def get_startup_details(
    startup_id: str,
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує детальну інформацію про стартап.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    result = get_startup_info(db, startup_id)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])

    # Додаємо інформацію про власника та ROI
    startup = db.query(Business).filter(Business.id == UUID(startup_id)).first()
    if startup:
        data = result["data"]
        data["is_owner"] = startup.owner_player_id == player.id
        data["owner_id"] = str(startup.owner_player_id) if startup.owner_player_id else None
        data["potential_roi"] = calculate_startup_roi(startup)

    return api_success(message="Інформація про стартап", data=result["data"])


@router.get("/available")
async def get_available_startups(
    city_id: str = None,
    stage: str = None,
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує список доступних для інвестування стартапів.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    result = list_available_startups(db, city_id, stage)

    return api_success(message="Список доступних стартапів", data=result["data"])


@router.get("/my-startups")
async def get_my_startups(
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує список стартапів гравця.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    startups = db.query(Business).filter(Business.owner_player_id == player.id, Business.is_startup).all()

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
                "cash_balance": float(startup.cash_balance),
                "funding_progress": float(startup.startup_funding) / float(stage_config["max_funding"]) * 100,
                "potential_roi": calculate_startup_roi(startup),
                "status": startup.status,
            }
        )

    return api_success(message="Ваші стартапи", data={"startups": result, "total_count": len(result)})


@router.get("/my-investments")
async def get_my_investments(
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Отримує список інвестицій гравця в чужі стартапи.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    # Знаходимо всі стартапи де гравець є інвестором
    all_startups = db.query(Business).filter(Business.is_startup, Business.status == "active").all()

    investments = []
    for startup in all_startups:
        if startup.startup_investors and str(player.id) in startup.startup_investors:
            stage_config = STARTUP_STAGES[startup.startup_stage]
            investment_amount = startup.startup_investors[str(player.id)]

            investments.append(
                {
                    "startup_id": str(startup.id),
                    "startup_name": startup.name,
                    "startup_type": startup.type,
                    "stage": startup.startup_stage,
                    "stage_name": stage_config["name"],
                    "investment_amount": investment_amount,
                    "total_funding": float(startup.startup_funding),
                    "success_chance": float(startup.startup_success_chance),
                    "potential_roi": calculate_startup_roi(startup),
                    "potential_return": investment_amount * calculate_startup_roi(startup),
                    "is_owner": startup.owner_player_id == player.id,
                }
            )

    return api_success(
        message="Ваші інвестиції",
        data={
            "investments": investments,
            "total_count": len(investments),
            "total_invested": sum(inv["investment_amount"] for inv in investments),
            "potential_total_return": sum(inv["potential_return"] for inv in investments),
        },
    )


@router.get("/stages")
async def get_startup_stages():
    """
    Отримує інформацію про етапи розвитку стартапів.
    """
    return api_success(message="Етапи стартапів", data=STARTUP_STAGES)


@router.get("/types")
async def get_startup_types():
    """
    Отримує інформацію про типи стартапів.
    """
    return api_success(message="Типи стартапів", data=STARTUP_TYPES)


@router.post("/{startup_id}/calculate-roi")
async def calculate_startup_roi_endpoint(
    startup_id: str,
    player_id: str = "",
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
    db: Session = Depends(get_db),
):
    """
    Розраховує потенційний ROI для стартапу.
    """
    player = require_player(db, player_id, player_token)
    if not player:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизований доступ")

    startup = db.query(Business).filter(Business.id == UUID(startup_id)).first()

    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Стартап не знайдено")

    roi = calculate_startup_roi(startup)

    return api_success(
        message="ROI розраховано",
        data={
            "startup_id": str(startup.id),
            "startup_name": startup.name,
            "potential_roi": roi,
            "stage": startup.startup_stage,
            "success_chance": float(startup.startup_success_chance),
        },
    )
