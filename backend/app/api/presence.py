"""API endpoints для відстеження присутності гравців"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.redis import PresenceService
from backend.app.database import get_db
from backend.app.repositories.player import PlayerRepository

router = APIRouter(prefix="/api/presence", tags=["presence"])


@router.get("/city/{city_id}/online/count")
async def get_online_players_count(city_id: str):
    """Отримати кількість онлайн гравців у місті"""
    count = await PresenceService.get_online_players_count(city_id)
    return {"success": True, "count": count}


@router.get("/city/{city_id}/online/players")
async def get_online_players(city_id: str, db: Session = Depends(get_db)):
    """Отримати список онлайн гравців у місті"""
    player_ids = await PresenceService.get_online_players(city_id)

    if not player_ids:
        return {"success": True, "players": []}

    # Отримуємо детальну інформацію про гравців
    player_repo = PlayerRepository(db)
    players = []

    for player_id in player_ids:
        player = player_repo.get_by_id(player_id)
        if player:
            players.append(
                {
                    "id": str(player.id),
                    "username": player.username,
                    "education": player.education,
                    "is_online": True,
                }
            )

    return {"success": True, "players": players}


@router.get("/global/online/count")
async def get_global_online_count():
    """Отримати загальну кількість онлайн гравців"""
    count = await PresenceService.get_online_players_count()
    return {"success": True, "count": count}


@router.get("/player/{player_id}/status")
async def get_player_presence_status(player_id: str):
    """Перевірити, чи гравець онлайн"""
    is_online = await PresenceService.is_player_online(player_id)
    return {"success": True, "is_online": is_online}


@router.post("/player/{player_id}/heartbeat")
async def player_heartbeat(player_id: str):
    """Оновити активність гравця (heartbeat)"""
    success = await PresenceService.update_player_activity(player_id)
    if success:
        return {"success": True, "message": "Activity updated"}
    else:
        raise HTTPException(status_code=404, detail="Player not found in presence system")
