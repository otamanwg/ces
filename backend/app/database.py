from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Apply Alembic migrations and fail fast when schema initialization is enabled."""
    project_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def get_db():
    """Залежність (Dependency) для отримання сесії БД у FastAPI ендпоінтах"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
