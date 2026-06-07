from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.middleware.request_logging import RequestLoggingMiddleware
from app.api.v1.router import api_router
from app.db.base import engine, Base
import app.models  # noqa: F401 — ensure all models are registered before create_all

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Monitour API (env=%s debug=%s)", settings.APP_ENV, settings.DEBUG)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        from app.db.init_db import auto_seed_plans, ensure_demo_users
        await ensure_demo_users()
        await auto_seed_plans()
        logger.info("Demo users and plans seed completed")
    except Exception as e:
        logger.warning("Startup seed failed: %s", e)
    yield
    logger.info("Shutting down Monitour API")


setup_logging(level=settings.LOG_LEVEL, app_env=settings.APP_ENV)


app = FastAPI(
    title="Monitour API",
    description="AI-Assisted Operations & Workforce Management Platform for Hotels & Hospitals",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
async def root():
    return {
        "product": "Monitour",
        "version": "1.0.0",
        "description": "AI-Assisted Operations & Workforce Management Platform",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Monitour API"}
