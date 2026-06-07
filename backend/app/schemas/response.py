from typing import Any

from pydantic import BaseModel, Field


class GameEffect(BaseModel):
    key: str
    label: str
    value: str
    delta: str | None = None


class ApiEnvelope(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    effects: list[GameEffect] = Field(default_factory=list)


def api_success(message: str, data: dict | None = None, effects: list | None = None) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data or {},
        "effects": effects or [],
    }


def api_error(message: str, data: dict | None = None) -> dict:
    return {
        "success": False,
        "message": message,
        "data": data or {},
        "effects": [],
    }
