import json

from backend.app.core.exceptions import GameException
from backend.main import game_exception_handler


def test_game_exception_handler_returns_api_error_envelope():
    response = game_exception_handler(None, GameException("Недостатньо коштів", {"required": 1200}))

    assert response.status_code == 200
    assert json.loads(response.body) == {
        "success": False,
        "message": "Недостатньо коштів",
        "data": {"required": 1200},
        "effects": [],
    }
