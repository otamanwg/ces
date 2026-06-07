"""
Тести для планувальника day tick.
"""

from unittest.mock import MagicMock, patch

from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.services.scheduler import (
    DAY_TICK_INTERVAL_SECONDS,
    _run_day_tick_for_all_cities,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)


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
        start_scheduler()
        scheduler = get_scheduler()
        assert scheduler.running
        stop_scheduler()
        assert not scheduler.running

    def test_start_idempotent(self):
        stop_scheduler()
        start_scheduler()
        start_scheduler()
        scheduler = get_scheduler()
        assert scheduler.running
        stop_scheduler()

    def test_job_registered(self):
        stop_scheduler()
        scheduler = get_scheduler()
        job_ids = [job.id for job in scheduler.get_jobs()]
        assert "day_tick_all_cities" in job_ids
        stop_scheduler()


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
