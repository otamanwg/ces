import os
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = "postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game"
UNSAFE_SECRET_FRAGMENTS = (
    "replace-with-",
    "city_dev_password",
    "ci-postgres-password",
    "ci-redis-password",
    "smoke-postgres-password",
    "smoke-redis-password",
    "drill-postgres-password",
    "drill-redis-password",
)


def _read_env_or_file(name: str, default: str | None = None) -> str | None:
    file_name = os.getenv(f"{name}_FILE")
    if file_name:
        try:
            value = Path(file_name).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(f"{name}_FILE could not be read.") from exc
        if not value:
            raise ValueError(f"{name}_FILE must not be empty.")
        return value
    return os.getenv(name, default)


try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


class Settings:
    def __init__(self) -> None:
        self.environment = os.getenv("CITY_ENV", "development").strip().lower()
        self.database_url = _read_env_or_file("CITY_DATABASE_URL", DEFAULT_DATABASE_URL) or DEFAULT_DATABASE_URL
        self.redis_url = _read_env_or_file("REDIS_URL", "redis://localhost:6379/0") or "redis://localhost:6379/0"
        self.release_sha = os.getenv("CITY_RELEASE_SHA", "dev").strip()
        self.release_image = os.getenv("CITY_RELEASE_IMAGE", "local").strip()
        self.release_version = os.getenv("CITY_RELEASE_VERSION", "0.3.0").strip()
        self.scheduler_lock_ttl_seconds = int(os.getenv("CITY_SCHEDULER_LOCK_TTL_SECONDS", "60"))
        self.scheduler_lock_renew_seconds = int(os.getenv("CITY_SCHEDULER_LOCK_RENEW_SECONDS", "15"))
        self.scheduler_lock_retry_seconds = int(os.getenv("CITY_SCHEDULER_LOCK_RETRY_SECONDS", "5"))
        self.log_format = os.getenv("CITY_LOG_FORMAT", "json" if self.is_production else "text").strip().lower()
        self.run_migrations_on_startup = os.getenv(
            "CITY_RUN_MIGRATIONS_ON_STARTUP",
            "false" if self.is_production else "true",
        ).lower() in {"1", "true", "yes", "on"}
        self.cors_origins = self._parse_origins(os.getenv("CITY_CORS_ORIGINS", "*"))
        self.debug = os.getenv("CITY_DEBUG", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.enable_frozen_routes = os.getenv(
            "CITY_ENABLE_FROZEN_ROUTES",
            "false" if self.is_production else "true",
        ).lower() in {"1", "true", "yes", "on"}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @staticmethod
    def _parse_origins(raw_value: str) -> list[str]:
        origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        return origins or ["*"]

    def validate(self) -> None:
        if not self.database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("CITY_DATABASE_URL must point to PostgreSQL. SQLite is not supported.")
        if not (0 < self.scheduler_lock_renew_seconds < self.scheduler_lock_ttl_seconds):
            raise ValueError(
                "CITY_SCHEDULER_LOCK_RENEW_SECONDS must be greater than zero "
                "and lower than CITY_SCHEDULER_LOCK_TTL_SECONDS."
            )
        if self.scheduler_lock_retry_seconds <= 0:
            raise ValueError("CITY_SCHEDULER_LOCK_RETRY_SECONDS must be greater than zero.")
        if self.log_format not in {"json", "text"}:
            raise ValueError("CITY_LOG_FORMAT must be either 'json' or 'text'.")
        if self.is_production:
            if "CITY_DATABASE_URL" not in os.environ and "CITY_DATABASE_URL_FILE" not in os.environ:
                raise ValueError("CITY_DATABASE_URL or CITY_DATABASE_URL_FILE is required in production.")
            if "REDIS_URL" not in os.environ and "REDIS_URL_FILE" not in os.environ:
                raise ValueError("REDIS_URL or REDIS_URL_FILE is required in production.")
            if "CITY_RELEASE_SHA" not in os.environ or not self.release_sha:
                raise ValueError("CITY_RELEASE_SHA is required in production.")
            if "CITY_RELEASE_IMAGE" not in os.environ or not self.release_image:
                raise ValueError("CITY_RELEASE_IMAGE is required in production.")
            if "CITY_RELEASE_VERSION" not in os.environ or not self.release_version:
                raise ValueError("CITY_RELEASE_VERSION is required in production.")
            self._validate_production_database_url()
            self._validate_production_redis_url()
            if self.debug:
                raise ValueError("CITY_DEBUG must be false in production.")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CITY_CORS_ORIGINS is not allowed in production.")
            for origin in self.cors_origins:
                if not origin.startswith("https://"):
                    raise ValueError("CITY_CORS_ORIGINS entries must use https:// in production.")

    def _validate_production_database_url(self) -> None:
        parsed = urlparse(self.database_url)
        if not parsed.username or not parsed.password:
            raise ValueError("CITY_DATABASE_URL must include username and password in production.")
        if any(fragment in self.database_url for fragment in UNSAFE_SECRET_FRAGMENTS):
            raise ValueError("CITY_DATABASE_URL contains a template or development credential.")

    def _validate_production_redis_url(self) -> None:
        parsed = urlparse(self.redis_url)
        if parsed.scheme != "redis":
            raise ValueError("REDIS_URL must use redis:// in production.")
        if not parsed.password:
            raise ValueError("REDIS_URL must include a password in production.")
        if any(fragment in self.redis_url for fragment in UNSAFE_SECRET_FRAGMENTS):
            raise ValueError("REDIS_URL contains a template or development credential.")


settings = Settings()
settings.validate()
