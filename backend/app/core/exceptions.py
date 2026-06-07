from typing import Any, Dict


class GameException(Exception):
    def __init__(self, message: str, data: Dict[str, Any] | None = None):
        self.message = message
        self.data = data or {}
        super().__init__(message)
