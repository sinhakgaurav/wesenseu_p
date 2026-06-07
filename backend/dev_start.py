"""
Dev startup script — patches PostgreSQL-specific types for SQLite dev mode.
Usage:  python dev_start.py
"""
import os
import sys

# Set dev environment if not already configured
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./monitour_dev.db")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-monitour-2026-do-not-use-in-prod")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Patch JSONB → JSON and PG UUID → String for SQLite compatibility BEFORE any model import
from sqlalchemy.types import TypeDecorator, String, JSON as SAJSON

class _UUIDStr(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, v, d): return str(v) if v is not None else None
    def process_result_value(self, v, d): return v

def _patch_types():
    from app.db.base import Base
    import app.models  # noqa: F401 — ensure all models registered
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = SAJSON()
            elif isinstance(col.type, PG_UUID):
                col.type = _UUIDStr()

_patch_types()

if __name__ == "__main__":
    import asyncio, uvicorn

    # Run table creation + seeding synchronously before the server starts
    async def _bootstrap():
        from app.db.base import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        from app.db.init_db import auto_seed_plans, ensure_cms_pages, ensure_demo_users
        await ensure_demo_users()
        await auto_seed_plans()
        await ensure_cms_pages()

    asyncio.run(_bootstrap())

    print("\n" + "="*60)
    print("  Monitour Dev Server")
    print("  DB   : SQLite (monitour_dev.db)")
    print("  API  : http://localhost:8000")
    print("  Docs : http://localhost:8000/api/docs")
    print("  Plans: auto-seeded on startup")
    print("="*60 + "\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
