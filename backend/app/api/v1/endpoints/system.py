"""System / database introspection and diagnostics (super_admin)."""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.employee import Employee
from app.services.diagnostics import MODULE_PROBES, run_all_diagnostics, run_single_module

router = APIRouter()


class DbColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool


class DbTableInfo(BaseModel):
    table_name: str
    row_count: int
    columns: List[DbColumnInfo]
    has_soft_delete: bool


class DbTablesResponse(BaseModel):
    schema_name: str
    table_count: int
    tables: List[DbTableInfo]


def _require_super_admin(current_user: Employee) -> None:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")


def _is_sqlite(db: AsyncSession) -> bool:
    bind = db.get_bind()
    return bind.dialect.name == "sqlite"


@router.get("/db-tables", response_model=DbTablesResponse)
async def list_database_tables(
    include_row_counts: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List database tables, columns, row counts, and soft-delete flags (PostgreSQL or SQLite dev)."""
    _require_super_admin(current_user)

    if _is_sqlite(db):
        tables_r = await db.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        table_names = [row[0] for row in tables_r.fetchall()]
        schema_name = "main"
    else:
        tables_r = await db.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
        )
        table_names = [row[0] for row in tables_r.fetchall()]
        schema_name = "public"

    out: List[DbTableInfo] = []
    for tname in table_names:
        if _is_sqlite(db):
            cols_r = await db.execute(text(f'PRAGMA table_info("{tname}")'))
            columns = [
                DbColumnInfo(name=row[1], type=row[2] or "TEXT", nullable=row[3] == 0)
                for row in cols_r.fetchall()
            ]
        else:
            cols_r = await db.execute(
                text(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :t
                    ORDER BY ordinal_position
                    """
                ),
                {"t": tname},
            )
            columns = [
                DbColumnInfo(
                    name=row[0],
                    type=row[1],
                    nullable=row[2] == "YES",
                )
                for row in cols_r.fetchall()
            ]
        col_names = {c.name for c in columns}
        has_soft = "is_active" in col_names and "deleted_at" in col_names

        row_count = 0
        if include_row_counts:
            try:
                cnt_r = await db.execute(
                    text(f'SELECT COUNT(*) FROM "{tname}"')
                )
                row_count = int(cnt_r.scalar() or 0)
            except Exception:
                row_count = -1

        out.append(
            DbTableInfo(
                table_name=tname,
                row_count=row_count,
                columns=columns,
                has_soft_delete=has_soft,
            )
        )

    return DbTablesResponse(schema_name=schema_name, table_count=len(out), tables=out)


@router.get("/diagnostics/modules")
async def list_diagnostic_modules(current_user: Employee = Depends(get_current_user)):
    """Catalog of probe targets for the diagnostics UI."""
    _require_super_admin(current_user)
    infra = [
        {"id": "postgres", "name": "PostgreSQL", "category": "infrastructure"},
        {"id": "redis", "name": "Redis", "category": "infrastructure"},
        {"id": "wesenseu", "name": "WesenseU AI", "category": "microservice"},
        {"id": "celery_broker", "name": "Celery broker", "category": "microservice"},
    ]
    modules = [{"id": p["id"], "name": p["name"], "category": "module"} for p in MODULE_PROBES]
    return {"modules": infra + modules}


@router.get("/diagnostics/run")
async def run_diagnostics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Run all infrastructure, microservice, and API module probes."""
    _require_super_admin(current_user)
    return await run_all_diagnostics(db, request.app)


@router.post("/diagnostics/run/{module_id}")
async def run_diagnostic_module(
    module_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Re-run a single probe (one module or infrastructure service)."""
    _require_super_admin(current_user)
    try:
        return await run_single_module(db, request.app, module_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
