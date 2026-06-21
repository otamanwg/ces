"""
Тести для планувальника day tick.
"""

from threading import Event
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.schedulers.background import BackgroundScheduler
from redis.exceptions import RedisError

from backend.app.services import scheduler as scheduler_module
from backend.app.services.scheduler import (
    DAY_TICK_INTERVAL_SECONDS,
    SCHEDULER_LEADER_KEY,
    SchedulerLeaderLock,
    _run_day_tick_for_all_cities,
    _run_scheduler_coordinator,
    _start_local_scheduler,
    _stop_local_scheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)


class FakeRedis:
    def __init__(self):
        self.values: dict[str, str] = {}
        self.closed = False

    def set(self, key, value, *, nx=False, px=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def eval(self, script, _key_count, key, owner_token, *args):
        if self.values.get(key) != owner_token:
            return 0
        if "pexpire" in script:
            return 1
        if "del" in script:
            del self.values[key]
            return 1
        raise AssertionError("Unexpected Redis script")

    def close(self):
        self.closed = True


class BrokenRedis(FakeRedis):
    def set(self, key, value, *, nx=False, px=None):
        raise RedisError("redis unavailable")


class OneCycleEvent(Event):
    def wait(self, timeout=None):
        self.set()
        return True


class TestSchedulerConfig:
    def test_interval_positive(self):
        assert DAY_TICK_INTERVAL_SECONDS > 0

    def test_interval_reasonable(self):
        assert 60 <= DAY_TICK_INTERVAL_SECONDS <= 3600

    def test_get_scheduler_returns_instance(self):
        stop_scheduler()
        scheduler = get_scheduler()
        assert scheduler is not None
        assert isinstance(scheduler, BackgroundScheduler)

    def test_get_scheduler_singleton(self):
        stop_scheduler()
        s1 = get_scheduler()
        s2 = get_scheduler()
        assert s1 is s2

    def test_start_stop(self):
        stop_scheduler()
        _start_local_scheduler()
        scheduler = get_scheduler()
        assert scheduler.running
        _stop_local_scheduler()
        assert not scheduler.running

    def test_start_idempotent(self):
        stop_scheduler()
        thread = MagicMock()
        thread.is_alive.return_value = True
        with (
            patch.object(scheduler_module, "_coordinator_thread", None),
            patch.object(scheduler_module, "_coordinator_stop", None),
            patch.object(scheduler_module, "Thread", return_value=thread) as thread_factory,
        ):
            start_scheduler()
            start_scheduler()
        thread_factory.assert_called_once()
        thread.start.assert_called_once()

    def test_job_registered(self):
        stop_scheduler()
        scheduler = get_scheduler()
        jobs = {job.id: job for job in scheduler.get_jobs()}
        assert "day_tick_all_cities" in jobs
        job = jobs["day_tick_all_cities"]
        assert job.max_instances == 1
        assert job.coalesce is True
        assert job.misfire_grace_time == DAY_TICK_INTERVAL_SECONDS - 1
        stop_scheduler()

    def test_stop_scheduler_waits_for_running_jobs(self):
        scheduler = MagicMock()
        scheduler.running = True

        with patch.object(scheduler_module, "_scheduler", scheduler):
            _stop_local_scheduler()
            scheduler.shutdown.assert_called_once_with(wait=True)
            assert scheduler_module._scheduler is None


class TestSchedulerLeaderLock:
    def test_single_owner_and_follower_takeover(self):
        client = FakeRedis()
        leader = SchedulerLeaderLock(client, ttl_seconds=60)
        follower = SchedulerLeaderLock(client, ttl_seconds=60)

        assert leader.acquire() is True
        assert follower.acquire() is False
        assert leader.renew() is True
        assert leader.release() is True
        assert follower.acquire() is True

    def test_stale_owner_cannot_release_successor(self):
        client = FakeRedis()
        stale = SchedulerLeaderLock(client, ttl_seconds=60)
        stale.owned = True
        client.values[SCHEDULER_LEADER_KEY] = "successor-token"

        assert stale.release() is False
        assert client.values[SCHEDULER_LEADER_KEY] == "successor-token"

    def test_acquisition_error_is_not_swallowed(self):
        lock = SchedulerLeaderLock(BrokenRedis(), ttl_seconds=60)
        with pytest.raises(RedisError):
            lock.acquire()

    def test_coordinator_fails_closed_when_redis_is_unavailable(self):
        client = BrokenRedis()
        stop_event = OneCycleEvent()

        with (
            patch("backend.app.services.scheduler.create_sync_redis_client", return_value=client),
            patch("backend.app.services.scheduler._start_local_scheduler") as start_local,
            patch("backend.app.services.scheduler._stop_local_scheduler") as stop_local,
        ):
            _run_scheduler_coordinator(stop_event)

        start_local.assert_not_called()
        stop_local.assert_called_once()
        assert client.closed is True


class TestRunDayTick:
    def test_skips_when_no_cities(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        with (
            patch("backend.app.services.scheduler.SessionLocal", return_value=mock_db),
            patch("backend.app.services.economy.game_day_tick"),
        ):
            _run_day_tick_for_all_cities()
        mock_db.close.assert_called()

    def test_calls_tick_for_each_city(self):
        city_a = MagicMock()
        city_a.id = "city-uuid-a"
        city_a.name = "TestCity"
        city_b = MagicMock()
        city_b.id = "city-uuid-b"
        city_b.name = "TestCity2"

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [city_a, city_b]

        tick_result = {"data": {"game_day": 1, "players_updated": 0}}

        with (
            patch("backend.app.services.scheduler.SessionLocal", return_value=mock_db),
            patch("backend.app.services.economy.game_day_tick", return_value=tick_result) as mock_tick,
        ):
            _run_day_tick_for_all_cities()

        assert mock_tick.call_count == 2
        mock_db.close.assert_called()

    def test_skips_city_when_postgres_advisory_lock_is_busy(self):
        city = MagicMock()
        city.id = "city-uuid-a"
        city.name = "BusyCity"

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [city]
        mock_db.execute.return_value.scalar.return_value = False

        with (
            patch("backend.app.services.scheduler.SessionLocal", return_value=mock_db),
            patch("backend.app.services.economy.game_day_tick") as mock_tick,
        ):
            _run_day_tick_for_all_cities()

        mock_tick.assert_not_called()
        mock_db.rollback.assert_called_once()

    def test_continues_on_city_error(self):
        city_a = MagicMock()
        city_a.id = "city-uuid-a"
        city_a.name = "BrokenCity"
        city_b = MagicMock()
        city_b.id = "city-uuid-b"
        city_b.name = "GoodCity"

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [city_a, city_b]

        tick_result = {"data": {"game_day": 1, "players_updated": 0}}

        def tick_side_effect(db, city_id):
            if city_id == "city-uuid-a":
                raise RuntimeError("DB error")
            return tick_result

        with (
            patch("backend.app.services.scheduler.SessionLocal", return_value=mock_db),
            patch("backend.app.services.economy.game_day_tick", side_effect=tick_side_effect) as mock_tick,
        ):
            _run_day_tick_for_all_cities()

        assert mock_tick.call_count == 2
        mock_db.close.assert_called()
