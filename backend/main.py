import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes.business_management import router as business_router
from backend.app.api.routes.frozen import router as frozen_router
from backend.app.api.routes.mvp import router as mvp_router
from backend.app.api.routes.startup_system import router as startup_router
from backend.app.core.config import settings
from backend.app.core.exceptions import GameException
from backend.app.database import get_db, init_db
from backend.app.realtime.manager import ws_manager
from backend.app.schemas.response import api_error
from backend.app.seed import seed_initial_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CityServer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("CITY_SKIP_DB_INIT", "").lower() in {"1", "true", "yes", "on"}:
        logger.info("Ініціалізацію бази даних пропущено через CITY_SKIP_DB_INIT.")
        yield
        return

    logger.info("Ініціалізація бази даних...")
    init_db()
    db = next(get_db())
    try:
        seed_initial_data(db)
    except Exception as e:
        logger.error(f"Помилка при сидінгу бази даних: {e}")
        db.rollback()
    finally:
        db.close()
    yield


app = FastAPI(
    title="City Economic Simulator Backend Engine",
    description="Backend для MVP економічного симулятора 'Місто'.",
    version="0.3.0",
    lifespan=lifespan,
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

app.include_router(mvp_router)
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
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "system",
                "content": f"Ви підключились до реалтайм мережі міста {city_id}.",
            }
        )
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "chat":
                await ws_manager.broadcast(
                    {
                        "type": "chat",
                        "sender": data.get("sender", "Громадянин"),
                        "text": data.get("text", ""),
                    }
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Помилка WebSocket зв'язку: {e}")
        ws_manager.disconnect(websocket)
