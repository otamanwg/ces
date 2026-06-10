"""Redis конфігурація та утиліти для кешування та presence"""

import json
import os
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis


class RedisManager:
    """Менеджер для роботи з Redis"""

    def __init__(self):
        self._redis: Redis | None = None

    async def connect(self) -> Redis:
        """Встановлення з'єднання з Redis"""
        if self._redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        return self._redis

    async def disconnect(self):
        """Закриття з'єднання"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def ping(self) -> bool:
        """Перевірка доступності Redis"""
        try:
            redis = await self.connect()
            await redis.ping()
            return True
        except Exception:
            return False


# Глобальний інстанс Redis менеджера
redis_manager = RedisManager()


class CacheService:
    """Сервіс для кешування даних"""

    # TTL для різних типів даних
    TTL_CITY_STATUS = 60  # 1 хвилина
    TTL_PLAYER_PROFILE = 300  # 5 хвилин
    TTL_PLAYER_REALTIME = 10  # 10 секунд для реального часу
    TTL_BUSINESS_LIST = 180  # 3 хвилини
    TTL_JOB_LIST = 120  # 2 хвилини

    @staticmethod
    async def get(key: str) -> Any | None:
        """Отримати дані з кешу"""
        try:
            r = await redis_manager.connect()
            data = await r.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Зберегти дані в кеш"""
        try:
            r = await redis_manager.connect()
            data = json.dumps(value, default=str)
            await r.set(key, data, ex=ttl)
            return True
        except Exception:
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """Видалити дані з кешу"""
        try:
            r = await redis_manager.connect()
            await r.delete(key)
            return True
        except Exception:
            return False

    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """Видалити дані за шаблоном"""
        try:
            r = await redis_manager.connect()
            keys = await r.keys(pattern)
            if keys:
                return await r.delete(*keys)
            return 0
        except Exception:
            return 0

    @staticmethod
    def make_city_key(city_id: str) -> str:
        """Створити ключ для статусу міста"""
        return f"city:{city_id}:status"

    @staticmethod
    def make_player_key(player_id: str) -> str:
        """Створити ключ для профілю гравця"""
        return f"player:{player_id}:profile"

    @staticmethod
    def make_player_realtime_key(player_id: str) -> str:
        """Створити ключ для реальних даних гравця"""
        return f"player:{player_id}:realtime"

    @staticmethod
    def make_business_list_key(city_id: str) -> str:
        """Створити ключ для списку бізнесів"""
        return f"city:{city_id}:businesses"

    @staticmethod
    def make_job_list_key(city_id: str) -> str:
        """Створити ключ для списку вакансій"""
        return f"city:{city_id}:jobs"


class PresenceService:
    """Сервіс для відстеження присутності гравців"""

    @staticmethod
    async def set_player_online(player_id: str, city_id: str, session_id: str = None) -> bool:
        """Позначити гравця як онлайн"""
        try:
            r = await redis_manager.connect()
            pipe = r.pipeline()

            # Зберігаємо інформацію про гравця
            player_data = {
                "player_id": player_id,
                "city_id": city_id,
                "session_id": session_id,
                "last_seen": str(datetime.utcnow()),
            }

            # Ключ гравця з TTL 5 хвилин
            pipe.set(f"presence:player:{player_id}", json.dumps(player_data), ex=300)

            # Додаємо до списку онлайн гравців міста
            pipe.sadd(f"presence:city:{city_id}:online", player_id)
            pipe.expire(f"presence:city:{city_id}:online", 300)

            # Додаємо до глобального списку онлайн гравців
            pipe.sadd("presence:global:online", player_id)
            pipe.expire("presence:global:online", 300)

            await pipe.execute()
            return True
        except Exception:
            return False

    @staticmethod
    async def set_player_offline(player_id: str, city_id: str = None) -> bool:
        """Позначити гравця як офлайн"""
        try:
            r = await redis_manager.connect()
            pipe = r.pipeline()

            # Видаляємо з присутності
            pipe.delete(f"presence:player:{player_id}")

            # Видаляємо зі списку онлайн гравців міста
            if city_id:
                pipe.srem(f"presence:city:{city_id}:online", player_id)
            else:
                # Якщо city_id не відомий, видаляємо з усіх міст
                cities = await r.keys("presence:city:*:online")
                for city_key in cities:
                    pipe.srem(city_key, player_id)

            # Видаляємо з глобального списку
            pipe.srem("presence:global:online", player_id)

            await pipe.execute()
            return True
        except Exception:
            return False

    @staticmethod
    async def is_player_online(player_id: str) -> bool:
        """Перевірити, чи гравець онлайн"""
        try:
            r = await redis_manager.connect()
            exists = await r.exists(f"presence:player:{player_id}")
            return bool(exists)
        except Exception:
            return False

    @staticmethod
    async def get_online_players_count(city_id: str = None) -> int:
        """Отримати кількість онлайн гравців"""
        try:
            r = await redis_manager.connect()
            if city_id:
                return await r.scard(f"presence:city:{city_id}:online")
            else:
                return await r.scard("presence:global:online")
        except Exception:
            return 0

    @staticmethod
    async def get_online_players(city_id: str = None) -> list[str]:
        """Отримати список ID онлайн гравців"""
        try:
            r = await redis_manager.connect()
            if city_id:
                return await r.smembers(f"presence:city:{city_id}:online")
            else:
                return await r.smembers("presence:global:online")
        except Exception:
            return []

    @staticmethod
    async def update_player_activity(player_id: str) -> bool:
        """Оновити час останньої активності гравця"""
        try:
            r = await redis_manager.connect()
            player_key = f"presence:player:{player_id}"

            # Отримуємо поточні дані
            data = await r.get(player_key)
            if data:
                player_data = json.loads(data)
                player_data["last_seen"] = str(datetime.utcnow())
                # Оновлюємо з тим самим TTL
                await r.set(player_key, json.dumps(player_data), ex=300)
                return True
            return False
        except Exception:
            return False


class SessionService:
    """Сервіс для управління сесіями (додатково до DB сесій)"""

    @staticmethod
    async def cache_session_data(player_id: str, session_data: dict[str, Any]) -> bool:
        """Кешувати дані сесії гравця"""
        try:
            r = await redis_manager.connect()
            key = f"session:{player_id}"
            # Сесія живе 24 години
            await r.set(key, json.dumps(session_data), ex=86400)
            return True
        except Exception:
            return False

    @staticmethod
    async def get_cached_session(player_id: str) -> dict[str, Any] | None:
        """Отримати кешовані дані сесії"""
        try:
            r = await redis_manager.connect()
            data = await r.get(f"session:{player_id}")
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    @staticmethod
    async def invalidate_session(player_id: str) -> bool:
        """Інвалідувати сесію гравця"""
        try:
            r = await redis_manager.connect()
            await r.delete(f"session:{player_id}")
            return True
        except Exception:
            return False


# Утиліти для інвалідації кешу
async def invalidate_player_cache(player_id: str):
    """Інвалідувати весь кеш гравця"""
    await CacheService.delete_pattern(f"player:{player_id}:*")
    await SessionService.invalidate_session(player_id)


async def invalidate_city_cache(city_id: str):
    """Інвалідувати весь кеш міста"""
    await CacheService.delete_pattern(f"city:{city_id}:*")
