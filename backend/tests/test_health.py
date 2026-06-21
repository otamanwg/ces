import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.responses import JSONResponse

from backend.app.api.health import health_check, liveness_check, readiness_check


def _schema_result(version: str = "test-schema-version") -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = version
    return result


def test_liveness_has_no_dependencies() -> None:
    result = asyncio.run(liveness_check())
    assert result["status"] == "alive"


def test_health_exposes_release_and_schema_metadata() -> None:
    db = MagicMock()
    db.execute.return_value = _schema_result("abc123")

    with patch("backend.app.api.health.redis_manager.ping", new=AsyncMock(return_value=True)):
        result = asyncio.run(health_check(db))

    assert result.status_code == 200
    assert result.body


def test_readiness_exposes_release_and_schema_metadata() -> None:
    db = MagicMock()
    db.execute.return_value = _schema_result("abc123")

    with patch("backend.app.api.health.redis_manager.ping", new=AsyncMock(return_value=True)):
        result = asyncio.run(readiness_check(db))

    assert result["status"] == "ready"
    assert result["schema_version"] == "abc123"
    assert result["release"]["sha"]


def test_readiness_returns_503_when_database_fails() -> None:
    db = MagicMock()
    db.execute.side_effect = RuntimeError("private database detail")

    result = asyncio.run(readiness_check(db))

    assert isinstance(result, JSONResponse)
    assert result.status_code == 503
    assert b"private database detail" not in result.body


def test_readiness_returns_503_when_redis_fails() -> None:
    db = MagicMock()
    with patch(
        "backend.app.api.health.redis_manager.ping",
        new=AsyncMock(return_value=False),
    ):
        result = asyncio.run(readiness_check(db))

    assert isinstance(result, JSONResponse)
    assert result.status_code == 503
    assert b"Required dependency is unavailable" in result.body
