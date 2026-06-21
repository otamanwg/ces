import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.main import websocket_city_hub


def test_invalid_websocket_token_closes_db_session() -> None:
    websocket = MagicMock()
    websocket.query_params = {"token": "invalid"}
    websocket.close = AsyncMock()
    db = MagicMock()

    with (
        patch("backend.main.get_db", return_value=iter([db])),
        patch("backend.app.repositories.player.PlayerRepository.get_by_token", return_value=None),
    ):
        asyncio.run(websocket_city_hub(websocket, "city-id"))

    websocket.close.assert_awaited_once_with(code=4002, reason="Invalid auth token")
    db.close.assert_called_once_with()


def test_websocket_setup_error_closes_db_session() -> None:
    websocket = MagicMock()
    websocket.query_params = {"token": "valid"}
    websocket.close = AsyncMock()
    db = MagicMock()
    player = MagicMock()

    with (
        patch("backend.main.get_db", return_value=iter([db])),
        patch("backend.app.repositories.player.PlayerRepository.get_by_token", return_value=player),
        patch(
            "backend.app.core.redis.PresenceService.set_player_online",
            new=AsyncMock(side_effect=RuntimeError("redis unavailable")),
        ),
    ):
        asyncio.run(websocket_city_hub(websocket, "city-id"))

    websocket.close.assert_awaited_once_with(code=4003, reason="Setup error")
    db.close.assert_called_once_with()
