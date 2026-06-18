import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.health import router as health_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.presence import router as presence_router
from backend.app.api.routes.business_management import router as business_router
from backend.app.api.routes.frozen import router as frozen_router
from backend.app.api.routes.mvp import router as mvp_router
from backend.app.api.routes.startup_system import router as startup_router
from backend.app.core.config import settings
from backend.app.core.exceptions import GameException
from backend.app.core.observability import configure_logging, observe_http_request
from backend.app.core.redis import redis_manager
from backend.app.database import engine, get_db, init_db
from backend.app.realtime.manager import ws_manager
from backend.app.schemas.response import api_error
from backend.app.seed import seed_initial_data
from backend.app.services.scheduler import start_scheduler, stop_scheduler

configure_logging()
logger = logging.getLogger("CityServer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if os.getenv("CITY_SKIP_DB_INIT", "").lower() in {"1", "true", "yes", "on"}:
            logger.info("Ініціалізацію бази даних пропущено через CITY_SKIP_DB_INIT.")
        else:
            if settings.run_migrations_on_startup:
                logger.info("Застосування Alembic міграцій під час startup...")
                init_db()
            else:
                logger.info("Alembic міграції під час startup вимкнені.")
            db = next(get_db())
            try:
                seed_initial_data(db)
            except Exception:
                logger.exception("Помилка при сидінгу бази даних.")
                db.rollback()
            finally:
                db.close()
            start_scheduler()
        yield
    finally:
        stop_scheduler()
        try:
            await redis_manager.disconnect()
        finally:
            engine.dispose()


app = FastAPI(
    title="City Economic Simulator Backend Engine",
    description="Backend для MVP економічного симулятора 'Місто'.",
    version="0.3.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)


# Глобальний обробник доменних помилок GameException
@app.exception_handler(GameException)
def game_exception_handler(request, exc: GameException):
    return JSONResponse(status_code=200, content=api_error(exc.message, exc.data))


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(observe_http_request)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(mvp_router)
app.include_router(presence_router)
if settings.enable_frozen_routes:
    app.include_router(frozen_router)
app.include_router(business_router, prefix="/api")
app.include_router(startup_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "status": "online",
        "engine": "FastAPI SQLAlchemy PostgreSQL",
        "target": "Godot Client C#",
        "mvp_api": "/api/player/register",
    }


@app.websocket("/ws/city/{city_id}")
async def websocket_city_hub(websocket: WebSocket, city_id: str):
    # Перевіряємо токен авторизації
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return

    # Отримуємо DB сесію
    db_gen = get_db()
    db = next(db_gen)

    try:
        try:
            # Знаходимо гравця за токеном
            from backend.app.repositories.player import PlayerRepository

            player = PlayerRepository(db).get_by_token(token)

            if not player:
                await websocket.close(code=4002, reason="Invalid auth token")
                return

            # Підключаємо до presence
            from backend.app.core.redis import PresenceService

            session_id = str(uuid4())
            await PresenceService.set_player_online(str(player.id), city_id, session_id)
        except Exception:
            logger.exception("Error in WebSocket setup")
            await websocket.close(code=4003, reason="Setup error")
            return

        await ws_manager.connect(websocket)

        try:
            # Відправляємо початкові дані
            online_count = await PresenceService.get_online_players_count(city_id)
            await websocket.send_json(
                {
                    "type": "system",
                    "content": f"Ви підключились до реалтайм мережі міста {city_id}.",
                    "online_players": online_count,
                }
            )

            # Сповіщаємо інших про нового гравця
            await ws_manager.broadcast(
                {
                    "type": "player_joined",
                    "player_id": str(player.id),
                    "username": player.username,
                    "online_count": online_count,
                }
            )

            while True:
                data = await websocket.receive_json()

                # Оновлюємо активність гравця
                await PresenceService.update_player_activity(str(player.id))

                if data.get("type") == "chat":
                    await ws_manager.broadcast(
                        {
                            "type": "chat",
                            "sender": player.username,
                            "sender_id": str(player.id),
                            "text": data.get("text", ""),
                            "timestamp": str(datetime.utcnow()),
                        }
                    )
                elif data.get("type") == "ping":
                    # Відповідаємо на ping для підтримки з'єднання
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            logger.info(f"Player {player.username} disconnected from city {city_id}")
            await PresenceService.set_player_offline(str(player.id), city_id)
            online_count = await PresenceService.get_online_players_count(city_id)
            await ws_manager.broadcast(
                {
                    "type": "player_left",
                    "player_id": str(player.id),
                    "username": player.username,
                    "online_count": online_count,
                }
            )
        except Exception:
            logger.exception("Помилка WebSocket зв'язку")
            await PresenceService.set_player_offline(str(player.id), city_id)
        finally:
            ws_manager.disconnect(websocket)
    finally:
        db.close()
