"""Health check endpoints for monitoring service status"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.redis import redis_manager
from backend.app.database import get_db

router = APIRouter(tags=["health"])


def _release_metadata() -> dict[str, str]:
    return {
        "version": settings.release_version,
        "sha": settings.release_sha,
        "image": settings.release_image,
    }


def _current_schema_version(db: Session) -> str | None:
    result = db.execute(text("SELECT version_num FROM alembic_version"))
    value = result.scalar_one_or_none()
    return str(value) if value is not None else None


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Основний health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.release_version,
        "release": _release_metadata(),
        "checks": {},
    }

    # Перевірка бази даних
    try:
        # Простий запит до БД
        schema_version = _current_schema_version(db)
        health_status["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
        health_status["checks"]["schema"] = {"status": "healthy", "version": schema_version}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # Перевірка Redis (опціонально)
    try:
        redis_available = await redis_manager.ping()
        if redis_available:
            health_status["checks"]["redis"] = {"status": "healthy", "message": "Redis connection successful"}
        else:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "message": "Redis connection failed (optional service)",
            }
    except Exception as e:
        # Redis не є критичним для базової роботи
        health_status["checks"]["redis"] = {
            "status": "degraded",
            "message": f"Redis connection error (optional service): {str(e)}",
        }

    # Повертаємо відповідний HTTP статус (тільки database failure робить unhealthy)
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe - перевіряє, чи готовий сервіс приймати трафік"""
    try:
        # Перевіряємо, що БД готова і схема мігрована.
        schema_version = _current_schema_version(db)

        # Перевіряємо Redis
        redis_ready = await redis_manager.ping()
        if not redis_ready:
            raise Exception("Redis not ready")

        return {
            "status": "ready",
            "timestamp": datetime.now(UTC).isoformat(),
            "release": _release_metadata(),
            "schema_version": schema_version,
        }
    except Exception:
        return JSONResponse(
            content={
                "status": "not_ready",
                "message": "Required dependency is unavailable.",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            status_code=503,
        )


@router.get("/health/live")
async def liveness_check():
    """Liveness probe - перевіряє, чи живий процес"""
    return {"status": "alive", "timestamp": datetime.now(UTC).isoformat()}
