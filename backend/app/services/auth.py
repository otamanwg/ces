import secrets

from sqlalchemy.orm import Session

from backend.app.models import Player
from backend.app.services.ids import to_uuid


def new_player_token() -> str:
    return secrets.token_urlsafe(32)


def get_authorized_player(db: Session, player_id: str, player_token: str | None) -> Player | None:
    if not player_token:
        return None

    return (
        db.query(Player)
        .filter(Player.id == to_uuid(player_id), Player.auth_token == player_token)
        .first()
    )
