from sqlalchemy.orm import Session

from backend.app.models import IdempotencyRecord
from backend.app.services.ids import to_uuid


def get_idempotent_response(
    db: Session,
    action: str,
    key: str | None,
    player_id: str | None = None,
) -> dict | None:
    if not key:
        return None

    query = db.query(IdempotencyRecord).filter(
        IdempotencyRecord.action == action,
        IdempotencyRecord.key == key,
    )
    if player_id:
        query = query.filter(IdempotencyRecord.player_id == to_uuid(player_id))
    else:
        query = query.filter(IdempotencyRecord.player_id.is_(None))

    record = query.first()
    if not record:
        return None
    return record.response_json


def save_idempotent_response(
    db: Session,
    action: str,
    key: str | None,
    player_id: str | None,
    response: dict,
) -> dict:
    if not key:
        return response

    record = IdempotencyRecord(
        action=action,
        key=key,
        player_id=to_uuid(player_id) if player_id else None,
        response_json=response,
    )
    db.add(record)
    db.commit()
    return response
