import logging
import sys
from contextlib import asynccontextmanager

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.research import router as research_router
from api.websocket import router as ws_router
from config import get_settings
from db.adapter import USE_SQLITE, close_db_pool, init_db_pool, init_schema

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s | %(message)s")
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting (env={settings.environment}, use_sqlite={USE_SQLITE})")

    if USE_SQLITE:
        await init_schema()
        logger.info("SQLite schema applied")

    await init_db_pool()
    logger.info("DB pool ready")
    yield
    await close_db_pool()


app = FastAPI(title="Research Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(research_router)
app.include_router(ws_router)
