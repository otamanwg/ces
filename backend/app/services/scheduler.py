"""
Планувальник фонових задач — автоматичний day tick для кожного міста.
Файл: backend/app/services/scheduler.py
"""

import logging
from contextlib import suppress
from datetime import UTC, datetime
from hashlib import blake2b
from threading import Event, Lock, Thread
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.redis import create_sync_redis_client
from backend.app.database import SessionLocal
from backend.app.models import City

logger = logging.getLogger("CityScheduler")

_scheduler: BackgroundScheduler | None = None
_coordinator_thread: Thread | None = None
_coordinator_stop: Event | None = None
_coordinator_state_lock = Lock()

DAY_TICK_INTERVAL_SECONDS = 300
SCHEDULER_LEADER_KEY = "city:scheduler:leader"

_RENEW_LEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('pexpire', KEYS[1], ARGV[2])
end
return 0
"""

_RELEASE_LEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


class SchedulerLeaderLock:
    """Token-checked Redis lease owned by one backend replica."""

    def __init__(
        self,
        client: Redis,
        *,
        key: str = SCHEDULER_LEADER_KEY,
        ttl_seconds: int | None = None,
    ) -> None:
        self.client = client
        self.key = key
        self.ttl_seconds = ttl_seconds or settings.scheduler_lock_ttl_seconds
        self.owner_token = uuid4().hex
        self.owned = False

    @property
    def ttl_milliseconds(self) -> int:
        return self.ttl_seconds * 1000

    def acquire(self) -> bool:
        self.owned = bool(
            self.client.set(
                self.key,
                self.owner_token,
                nx=True,
                px=self.ttl_milliseconds,
            )
        )
        return self.owned

    def renew(self) -> bool:
        if not self.owned:
            return False
        renewed = bool(
            self.client.eval(
                _RENEW_LEASE_SCRIPT,
                1,
                self.key,
                self.owner_token,
                self.ttl_milliseconds,
            )
        )
        self.owned = renewed
        return renewed

    def release(self) -> bool:
        if not self.owned:
            return False
        try:
            return bool(
                self.client.eval(
                    _RELEASE_LEASE_SCRIPT,
                    1,
                    self.key,
                    self.owner_token,
                )
            )
        finally:
            self.owned = False


def _city_advisory_lock_key(city_id: str) -> int:
    digest = blake2b(
        f"city-day-tick:{city_id}".encode(),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, byteorder="big", signed=True)


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
            lock_acquired = bool(
                db.execute(
                    text("SELECT pg_try_advisory_xact_lock(:lock_key)"),
                    {"lock_key": _city_advisory_lock_key(city_id)},
                ).scalar()
            )
            if not lock_acquired:
                logger.info(
                    "Scheduler: місто '%s' уже обробляє інша replica.",
                    city_name,
                )
                db.rollback()
                continue

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
            max_instances=1,
            coalesce=True,
            misfire_grace_time=DAY_TICK_INTERVAL_SECONDS - 1,
        )
    return _scheduler


def _start_local_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info(
            "Scheduler запущено. Day tick кожні %d сек.",
            DAY_TICK_INTERVAL_SECONDS,
        )


def _stop_local_scheduler() -> None:
    global _scheduler
    scheduler = _scheduler
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler зупинено.")
    finally:
        _scheduler = None


def _run_scheduler_coordinator(stop_event: Event) -> None:
    client: Redis | None = None
    leader_lock: SchedulerLeaderLock | None = None
    try:
        client = create_sync_redis_client()
        leader_lock = SchedulerLeaderLock(client)

        while not stop_event.is_set():
            try:
                if leader_lock.owned:
                    if not leader_lock.renew():
                        logger.warning("Scheduler leadership втрачено.")
                        _stop_local_scheduler()
                elif leader_lock.acquire():
                    logger.info("Scheduler leadership отримано.")
                    _start_local_scheduler()
            except RedisError:
                logger.exception("Scheduler leadership Redis operation failed.")
                if leader_lock.owned:
                    leader_lock.owned = False
                    _stop_local_scheduler()

            wait_seconds = (
                settings.scheduler_lock_renew_seconds if leader_lock.owned else settings.scheduler_lock_retry_seconds
            )
            stop_event.wait(wait_seconds)
    finally:
        _stop_local_scheduler()
        if leader_lock and leader_lock.owned:
            with suppress(RedisError):
                leader_lock.release()
        if client is not None:
            with suppress(RedisError):
                client.close()


def start_scheduler() -> None:
    global _coordinator_thread, _coordinator_stop
    with _coordinator_state_lock:
        if _coordinator_thread and _coordinator_thread.is_alive():
            return

        _coordinator_stop = Event()
        _coordinator_thread = Thread(
            target=_run_scheduler_coordinator,
            args=(_coordinator_stop,),
            name="city-scheduler-leader",
            daemon=True,
        )
        _coordinator_thread.start()
        logger.info("Scheduler leader coordinator запущено.")


def stop_scheduler() -> None:
    global _coordinator_thread, _coordinator_stop
    with _coordinator_state_lock:
        thread = _coordinator_thread
        stop_event = _coordinator_stop
        _coordinator_thread = None
        _coordinator_stop = None

    if stop_event:
        stop_event.set()
    if thread and thread.is_alive():
        thread.join(timeout=settings.scheduler_lock_ttl_seconds)
        if thread.is_alive():
            logger.error("Scheduler leader coordinator не завершився вчасно.")
            return

    _stop_local_scheduler()
