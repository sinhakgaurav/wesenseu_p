"""Health probes for infrastructure and API modules."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Awaitable, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


@dataclass
class ProbeResult:
    id: str
    name: str
    category: str  # infrastructure | microservice | module
    status: str  # ok | warn | error | skip
    latency_ms: float
    message: str
    detail: Optional[dict[str, Any]] = None


MODULE_PROBES: list[dict[str, Any]] = [
    {"id": "auth", "name": "Authentication", "method": "POST", "path": "/api/v1/auth/login", "public": True, "body": {"email": "admin@monitour.in", "password": "Admin@2026"}},
    {"id": "properties", "name": "Properties", "method": "GET", "path": "/api/v1/properties/", "auth": True},
    {"id": "rooms", "name": "Rooms", "method": "GET", "path": "/api/v1/rooms/?limit=1", "auth": True, "property_query": True},
    {"id": "tasks", "name": "Tasks", "method": "GET", "path": "/api/v1/tasks/?limit=1", "auth": True, "property_query": True},
    {"id": "tickets", "name": "Tickets", "method": "GET", "path": "/api/v1/tickets/?limit=1", "auth": True, "property_query": True},
    {"id": "employees", "name": "Employees", "method": "GET", "path": "/api/v1/employees/?limit=1", "auth": True, "property_query": True},
    {"id": "inventory", "name": "Inventory", "method": "GET", "path": "/api/v1/inventory/items?limit=1", "auth": True, "property_query": True},
    {"id": "orders", "name": "Orders", "method": "GET", "path": "/api/v1/orders/?limit=1", "auth": True, "property_query": True},
    {"id": "feedback", "name": "Feedback", "method": "GET", "path": "/api/v1/feedback/?limit=1", "auth": True, "property_query": True},
    {"id": "attendance", "name": "Attendance", "method": "GET", "path": "/api/v1/attendance/summary", "auth": True, "property_query": True},
    {"id": "reports", "name": "Reports", "method": "GET", "path": "/api/v1/reports/occupancy?days=7", "auth": True, "property_query": True},
    {"id": "dashboard", "name": "Dashboard", "method": "GET", "path": "/api/v1/dashboard/platform", "auth": True},
    {"id": "plans", "name": "Plans (public)", "method": "GET", "path": "/api/v1/plans", "public": True},
    {"id": "pages", "name": "CMS Pages", "method": "GET", "path": "/api/v1/pages/slug/about", "public": True},
    {"id": "catalog", "name": "Catalog", "method": "GET", "path": "/api/v1/catalog/items?kind=amenity", "auth": True},
    {"id": "vendors", "name": "Vendors", "method": "GET", "path": "/api/v1/vendors/?limit=1", "auth": True, "property_query": True},
    {"id": "laundry", "name": "Laundry", "method": "GET", "path": "/api/v1/laundry?limit=1", "auth": True, "property_query": True},
    {"id": "surveillance", "name": "Surveillance", "method": "GET", "path": "/api/v1/surveillance/cameras?limit=1", "auth": True, "property_query": True},
    {"id": "benchmarks", "name": "Benchmarks", "method": "GET", "path": "/api/v1/benchmarks/categories", "auth": True, "property_query": True},
    {"id": "admin", "name": "Super Admin", "method": "GET", "path": "/api/v1/admin/stats", "auth": True},
    {"id": "system", "name": "System / DB", "method": "GET", "path": "/api/v1/system/db-tables", "auth": True},
    {"id": "customers", "name": "Customers (admin)", "method": "GET", "path": "/api/v1/admin/customers", "auth": True},
    {"id": "property_groups", "name": "Property Groups", "method": "GET", "path": "/api/v1/property-groups/?limit=1", "auth": True},
    {"id": "departments", "name": "Departments", "method": "GET", "path": "/api/v1/departments/?limit=1", "auth": True, "property_query": True},
    {"id": "room_categories", "name": "Room Categories", "method": "GET", "path": "/api/v1/room-categories/?limit=1", "auth": True, "property_query": True},
    {"id": "notifications", "name": "Notifications", "method": "GET", "path": "/api/v1/notifications/?limit=1", "auth": True},
    {"id": "guest_stays", "name": "Guest Stays", "method": "GET", "path": "/api/v1/guest-stays/?limit=1", "auth": True, "property_query": True},
    {"id": "onboarding", "name": "Onboarding", "method": "GET", "path": "/api/v1/onboarding/steps", "auth": True},
    {"id": "task_sla", "name": "Task SLA Policies", "method": "GET", "path": "/api/v1/task-sla-policies", "auth": True, "property_query": True},
    {"id": "support", "name": "Support (admin)", "method": "GET", "path": "/api/v1/support/admin/conversations", "auth": True},
    {"id": "fb", "name": "F&B Outlets", "method": "GET", "path": "/api/v1/fb/properties/{property_id}/outlets", "auth": True, "property_path": True},
    {"id": "contacts", "name": "Property Contacts", "method": "GET", "path": "/api/v1/contacts/properties/{property_id}", "auth": True, "property_path": True},
]


_DEBUG_LOG = Path(__file__).resolve().parents[3] / "debug-4bdc7f.log"


def _agent_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "4bdc7f",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion


async def probe_postgres(db: AsyncSession) -> ProbeResult:
    start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        ms = (time.perf_counter() - start) * 1000
        return ProbeResult("postgres", "PostgreSQL", "infrastructure", "ok", ms, "Connected")
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        return ProbeResult("postgres", "PostgreSQL", "infrastructure", "error", ms, str(e))


async def probe_redis() -> ProbeResult:
    start = time.perf_counter()
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pong = await client.ping()
        await client.aclose()
        ms = (time.perf_counter() - start) * 1000
        status = "ok" if pong else "warn"
        return ProbeResult("redis", "Redis", "infrastructure", status, ms, "PONG" if pong else "No response")
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        st = "warn" if settings.APP_ENV == "development" else "error"
        msg = f"Not running (dev): {e}" if st == "warn" else str(e)
        return ProbeResult("redis", "Redis", "infrastructure", st, ms, msg)


async def probe_wesenseu() -> ProbeResult:
    start = time.perf_counter()
    base = settings.WESENSEU_API_URL.rstrip("/")
    # API may be mounted at /api/v1 — health is usually at service root
    health_url = base.replace("/api/v1", "") + "/health"
    if not health_url.startswith("http"):
        health_url = "http://localhost:8001/health"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(health_url)
        ms = (time.perf_counter() - start) * 1000
        if r.status_code == 200:
            return ProbeResult(
                "wesenseu",
                "WesenseU AI",
                "microservice",
                "ok",
                ms,
                "Reachable",
                {"url": health_url, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:200]},
            )
        return ProbeResult("wesenseu", "WesenseU AI", "microservice", "warn", ms, f"HTTP {r.status_code}", {"url": health_url})
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        st = "warn" if settings.APP_ENV == "development" else "error"
        msg = f"Not running (dev): {e}" if st == "warn" else str(e)
        return ProbeResult("wesenseu", "WesenseU AI", "microservice", st, ms, msg, {"url": health_url})


async def probe_celery_broker() -> ProbeResult:
    """Redis broker reachability (Celery workers use same Redis)."""
    start = time.perf_counter()
    try:
        import redis

        client = redis.from_url(settings.CELERY_BROKER_URL)
        client.ping()
        ms = (time.perf_counter() - start) * 1000
        return ProbeResult("celery_broker", "Celery broker (Redis)", "microservice", "ok", ms, "Broker reachable")
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        st = "warn" if settings.APP_ENV == "development" else "error"
        msg = f"Not running (dev): {e}" if st == "warn" else str(e)
        return ProbeResult("celery_broker", "Celery broker (Redis)", "microservice", st, ms, msg)


async def _login_token(client: httpx.AsyncClient) -> Optional[str]:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@monitour.in", "password": "Admin@2026"},
    )
    if r.status_code != 200:
        return None
    return r.json().get("access_token")


async def _first_property_id(client: httpx.AsyncClient, headers: dict) -> Optional[str]:
    r = await client.get("/api/v1/properties/", headers=headers)
    if r.status_code != 200:
        return None
    data = r.json()
    if isinstance(data, list) and data:
        return str(data[0].get("id"))
    return None


async def probe_http_module(
    client: httpx.AsyncClient,
    probe: dict[str, Any],
    headers: dict,
    property_id: Optional[str],
) -> ProbeResult:
    start = time.perf_counter()
    path = probe["path"]
    if probe.get("property_path") and property_id:
        path = path.replace("{property_id}", property_id)
    elif probe.get("property_path") and not property_id:
        _agent_log("B", "diagnostics.py:probe_http_module", "skip property_path probe", {"id": probe["id"]})
        return ProbeResult(probe["id"], probe["name"], "module", "skip", 0, "No property_id for path-scoped probe")
    if probe.get("property_query") and property_id:
        sep = "&" if "?" in path else "?"
        path = f"{path}{sep}property_id={property_id}"

    method = probe.get("method", "GET").upper()
    try:
        if probe.get("public"):
            if method == "POST":
                r = await client.post(path, json=probe.get("body", {}))
            else:
                r = await client.get(path)
        else:
            if method == "POST":
                r = await client.post(path, json=probe.get("body", {}), headers=headers)
            else:
                r = await client.get(path, headers=headers)

        ms = (time.perf_counter() - start) * 1000
        _agent_log(
            "A" if r.status_code == 307 else "D",
            "diagnostics.py:probe_http_module",
            "probe response",
            {"id": probe["id"], "path": path, "status": r.status_code, "latency_ms": round(ms, 1)},
        )
        if r.status_code in (200, 201):
            return ProbeResult(probe["id"], probe["name"], "module", "ok", ms, f"HTTP {r.status_code}")
        if r.status_code == 404 and probe["id"] == "pages":
            return ProbeResult(probe["id"], probe["name"], "module", "warn", ms, "CMS page not seeded (404)")
        if r.status_code in (401, 403):
            return ProbeResult(probe["id"], probe["name"], "module", "error", ms, f"Auth failed ({r.status_code})")
        if r.status_code == 307:
            return ProbeResult(
                probe["id"],
                probe["name"],
                "module",
                "error",
                ms,
                "Trailing-slash redirect (307) — fix API URL",
                {"location": r.headers.get("location")},
            )
        return ProbeResult(
            probe["id"],
            probe["name"],
            "module",
            "warn" if r.status_code < 500 else "error",
            ms,
            f"HTTP {r.status_code}",
            {"body": r.text[:300]},
        )
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        return ProbeResult(probe["id"], probe["name"], "module", "error", ms, str(e))


async def run_all_diagnostics(db: AsyncSession, app) -> dict[str, Any]:
    from httpx import ASGITransport

    results: list[ProbeResult] = []
    results.append(await probe_postgres(db))
    results.append(await probe_redis())
    results.append(await probe_wesenseu())
    results.append(await probe_celery_broker())

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        token = await _login_token(client)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        property_id = await _first_property_id(client, headers) if token else None
        _agent_log("C", "diagnostics.py:run_all_diagnostics", "auth context", {"has_token": bool(token), "property_id": property_id})

        if not token:
            results.append(
                ProbeResult("auth", "Authentication", "module", "error", 0, "Demo login failed — cannot probe modules")
            )
        else:
            for probe in MODULE_PROBES:
                if probe["id"] == "auth":
                    results.append(
                        ProbeResult("auth", "Authentication", "module", "ok", 0, "Login OK")
                    )
                    continue
                results.append(await probe_http_module(client, probe, headers, property_id))

    def serialize(p: ProbeResult) -> dict:
        return {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "status": p.status,
            "latency_ms": round(p.latency_ms, 1),
            "message": p.message,
            "detail": p.detail,
        }

    items = [serialize(p) for p in results]
    ok = sum(1 for p in results if p.status == "ok")
    err = sum(1 for p in results if p.status == "error")
    warn = sum(1 for p in results if p.status == "warn")

    return {
        "summary": {"total": len(items), "ok": ok, "warn": warn, "error": err},
        "property_id_used": property_id,
        "checks": items,
    }


def _serialize_probe(p: ProbeResult) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "status": p.status,
        "latency_ms": round(p.latency_ms, 1),
        "message": p.message,
        "detail": p.detail,
    }


async def run_single_module(db: AsyncSession, app, module_id: str) -> dict[str, Any]:
    from httpx import ASGITransport

    if module_id == "postgres":
        return {"check": _serialize_probe(await probe_postgres(db))}
    if module_id == "redis":
        return {"check": _serialize_probe(await probe_redis())}
    if module_id == "wesenseu":
        return {"check": _serialize_probe(await probe_wesenseu())}
    if module_id == "celery_broker":
        return {"check": _serialize_probe(await probe_celery_broker())}

    probe = next((p for p in MODULE_PROBES if p["id"] == module_id), None)
    if not probe:
        raise ValueError(f"Unknown module: {module_id}")

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        token = await _login_token(client)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        property_id = await _first_property_id(client, headers) if token else None
        if probe["id"] == "auth" and token:
            r = ProbeResult("auth", "Authentication", "module", "ok", 0, "Login OK")
        elif not token:
            r = ProbeResult(module_id, probe["name"], "module", "error", 0, "Not authenticated")
        else:
            r = await probe_http_module(client, probe, headers, property_id)

    return {"check": _serialize_probe(r)}
