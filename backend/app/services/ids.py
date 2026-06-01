import uuid


def to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def try_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    try:
        return to_uuid(value)
    except (TypeError, ValueError, AttributeError):
        return None
