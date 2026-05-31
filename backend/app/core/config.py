import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = "postgresql+psycopg2://city:city_dev_password@127.0.0.1:5432/city_game"

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("CITY_DATABASE_URL", DEFAULT_DATABASE_URL)
        self.cors_origins = self._parse_origins(os.getenv("CITY_CORS_ORIGINS", "*"))
        self.debug = os.getenv("CITY_DEBUG", "true").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _parse_origins(raw_value: str) -> list[str]:
        origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        return origins or ["*"]

    def validate(self) -> None:
        if not self.database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("CITY_DATABASE_URL must point to PostgreSQL. SQLite is not supported.")


settings = Settings()
settings.validate()
