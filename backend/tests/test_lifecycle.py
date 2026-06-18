import asyncio
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import backend.main as main


def _record(events: list[str], name: str) -> Callable[..., None]:
    def record(*_args: object, **_kwargs: object) -> None:
        events.append(name)

    return record


def _lifecycle_patches(events: list[str]):
    db = MagicMock()
    db.close.side_effect = _record(events, "db.close")

    async def disconnect() -> None:
        events.append("redis.disconnect")

    return (
        db,
        patch.object(main, "init_db", side_effect=_record(events, "init_db")),
        patch.object(main, "get_db", return_value=iter([db])),
        patch.object(main, "seed_initial_data", side_effect=_record(events, "seed")),
        patch.object(main, "start_scheduler", side_effect=_record(events, "start_scheduler")),
        patch.object(main, "stop_scheduler", side_effect=_record(events, "stop_scheduler")),
        patch.object(main.redis_manager, "disconnect", new=AsyncMock(side_effect=disconnect)),
        patch.object(main.engine, "dispose", side_effect=_record(events, "engine.dispose")),
    )


def test_lifespan_runs_startup_and_cleanup_in_order() -> None:
    events: list[str] = []
    db, init_db, get_db, seed, start, stop, disconnect, dispose = _lifecycle_patches(events)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            events.append("body")

    with (
        patch.dict("os.environ", {"CITY_SKIP_DB_INIT": "false"}),
        patch.object(main.settings, "run_migrations_on_startup", True),
        init_db,
        get_db,
        seed,
        start,
        stop,
        disconnect,
        dispose,
    ):
        asyncio.run(run_lifespan())

    assert events == [
        "init_db",
        "seed",
        "db.close",
        "start_scheduler",
        "body",
        "stop_scheduler",
        "redis.disconnect",
        "engine.dispose",
    ]
    db.rollback.assert_not_called()


def test_lifespan_cleans_up_when_body_raises() -> None:
    events: list[str] = []
    _, init_db, get_db, seed, start, stop, disconnect, dispose = _lifecycle_patches(events)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            events.append("body")
            raise RuntimeError("lifespan body failed")

    with (
        patch.dict("os.environ", {"CITY_SKIP_DB_INIT": "false"}),
        patch.object(main.settings, "run_migrations_on_startup", True),
        init_db,
        get_db,
        seed,
        start,
        stop,
        disconnect,
        dispose,
        pytest.raises(RuntimeError, match="lifespan body failed"),
    ):
        asyncio.run(run_lifespan())

    assert events[-3:] == [
        "stop_scheduler",
        "redis.disconnect",
        "engine.dispose",
    ]


def test_lifespan_can_skip_startup_migrations_without_skipping_seed_or_scheduler() -> None:
    events: list[str] = []
    _, init_db, get_db, seed, start, stop, disconnect, dispose = _lifecycle_patches(events)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            events.append("body")

    with (
        patch.dict("os.environ", {"CITY_SKIP_DB_INIT": "false"}),
        patch.object(main.settings, "run_migrations_on_startup", False),
        init_db as init_db_mock,
        get_db,
        seed,
        start,
        stop,
        disconnect,
        dispose,
    ):
        asyncio.run(run_lifespan())

    init_db_mock.assert_not_called()
    assert events == [
        "seed",
        "db.close",
        "start_scheduler",
        "body",
        "stop_scheduler",
        "redis.disconnect",
        "engine.dispose",
    ]


def test_skip_db_init_still_runs_teardown() -> None:
    events: list[str] = []
    _, init_db, get_db, seed, start, stop, disconnect, dispose = _lifecycle_patches(events)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            events.append("body")

    with (
        patch.dict("os.environ", {"CITY_SKIP_DB_INIT": "true"}),
        init_db as init_db_mock,
        get_db as get_db_mock,
        seed as seed_mock,
        start as start_mock,
        stop,
        disconnect,
        dispose,
    ):
        asyncio.run(run_lifespan())

    init_db_mock.assert_not_called()
    get_db_mock.assert_not_called()
    seed_mock.assert_not_called()
    start_mock.assert_not_called()
    assert events == [
        "body",
        "stop_scheduler",
        "redis.disconnect",
        "engine.dispose",
    ]
