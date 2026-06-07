import secrets

from sqlalchemy.orm import Session

from backend.app.models import Player
from backend.app.repositories.player import PlayerRepository
from backend.app.services.ids import try_uuid


def new_player_token() -> str:
    return secrets.token_urlsafe(32)


def get_authorized_player(
    db: Session, player_id: str, player_token: str | None
) -> Player | None:
    if not player_token:
        return None
    player_uuid = try_uuid(player_id)
    if player_uuid is None:
        return None

    return PlayerRepository(db).get_by_auth_token(player_uuid, player_token)
