from typing import Any


class GameException(Exception):
    def __init__(self, message: str, data: dict[str, Any] | None = None):
        self.message = message
        self.data = data or {}
        super().__init__(message)
