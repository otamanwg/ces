from sqlalchemy.orm import Session

from backend.app.models import Player
from backend.app.schemas.mvp import PlayerSnapshotData
from backend.app.schemas.response import api_success
from backend.app.services.idempotency import save_idempotent_response
from backend.app.services.player_profile import build_player_snapshot
from backend.app.services.player_progress import build_goal_effects


def build_player_action_response(
    db: Session,
    player: Player,
    message: str,
    response_model=PlayerSnapshotData,
    **extras,
) -> dict:
    snapshot = build_player_snapshot(db, player)
    payload = response_model(**snapshot, **extras).model_dump()
    return api_success(message, payload, build_goal_effects(db, player))


def save_player_action_response(
    db: Session,
    action: str,
    idempotency_key: str | None,
    player_id: str,
    player: Player,
    message: str,
    response_model=PlayerSnapshotData,
    **extras,
) -> dict:
    response = build_player_action_response(db, player, message, response_model, **extras)
    return save_idempotent_response(db, action, idempotency_key, player_id, response)
