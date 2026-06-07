"""
Планувальник фонових задач — автоматичний day tick для кожного міста.
Файл: backend/app/services/scheduler.py
"""

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.database import SessionLocal
from backend.app.models import City

logger = logging.getLogger("CityScheduler")

_scheduler: BackgroundScheduler | None = None

DAY_TICK_INTERVAL_SECONDS = 300


def _run_day_tick_for_all_cities() -> None:
    """Синхронна функція що викликається scheduler-ом."""
    from backend.app.services.economy import game_day_tick

    city_ids: list[tuple[str, str]] = []
    db = SessionLocal()
    try:
        cities = db.query(City).all()
        city_ids = [(str(c.id), c.name) for c in cities]
    finally:
        db.close()

    if not city_ids:
        logger.info("Scheduler: міст не знайдено, пропускаємо tick.")
        return

    for city_id, city_name in city_ids:
        db = SessionLocal()
        try:
            result = game_day_tick(db, city_id)
            db.commit()
            day = result.get("data", {}).get("game_day", "?")
            players = result.get("data", {}).get("players_updated", 0)
            logger.info(
                "Scheduler: tick міста '%s' день=%s гравці=%s",
                city_name,
                day,
                players,
            )
        except Exception as e:
            logger.error("Scheduler: помилка tick міста '%s': %s", city_name, e)
            db.rollback()
        finally:
            db.close()


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.add_job(
            _run_day_tick_for_all_cities,
            trigger=IntervalTrigger(seconds=DAY_TICK_INTERVAL_SECONDS),
            id="day_tick_all_cities",
            name="Day tick для всіх активних міст",
            replace_existing=True,
            next_run_time=datetime.now(UTC),
        )
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info(
            "Scheduler запущено. Day tick кожні %d сек.",
            DAY_TICK_INTERVAL_SECONDS,
        )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler зупинено.")
    _scheduler = None
