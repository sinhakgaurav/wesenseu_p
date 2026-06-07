"""Integration tests against running Monitour API (Docker or local uvicorn)."""
from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health(http_client: httpx.AsyncClient):
    r = await http_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["service"] == "Monitour API"


@pytest.mark.asyncio
async def test_root(http_client: httpx.AsyncClient):
    r = await http_client.get("/")
    assert r.status_code == 200
    assert r.json()["product"] == "Monitour"


@pytest.mark.asyncio
async def test_login_invalid(http_client: httpx.AsyncClient):
    r = await http_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_demo_user(http_client: httpx.AsyncClient):
    from tests.conftest import DEMO_EMAIL, DEMO_PASSWORD

    r = await http_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data["user"]["role"] == "super_admin"


@pytest.mark.asyncio
async def test_public_plans(http_client: httpx.AsyncClient):
    r = await http_client.get("/api/v1/plans")
    assert r.status_code == 200
    plans = r.json()
    assert isinstance(plans, list)
    assert len(plans) >= 1


@pytest.mark.asyncio
async def test_public_cms_about(http_client: httpx.AsyncClient):
    r = await http_client.get("/api/v1/pages/slug/about")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        page = r.json()
        assert page["slug"] == "about"


@pytest.mark.asyncio
async def test_dashboard_platform_requires_auth(http_client: httpx.AsyncClient):
    r = await http_client.get("/api/v1/dashboard/platform")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_platform_authenticated(http_client: httpx.AsyncClient, auth_headers: dict):
    r = await http_client.get("/api/v1/dashboard/platform", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "total_properties" in data
    assert "properties" in data


@pytest.mark.asyncio
async def test_properties_list(http_client: httpx.AsyncClient, auth_headers: dict):
    r = await http_client.get("/api/v1/properties/", headers=auth_headers)
    assert r.status_code == 200, r.text
    props = r.json()
    assert isinstance(props, list)


@pytest.mark.asyncio
async def test_tasks_with_property_scope(http_client: httpx.AsyncClient, auth_headers: dict):
    props_r = await http_client.get("/api/v1/properties/", headers=auth_headers)
    assert props_r.status_code == 200
    props = props_r.json()
    if not props:
        pytest.skip("No properties in database")
    prop_id = props[0]["id"]
    r = await http_client.get(
        f"/api/v1/tasks?property_id={prop_id}&limit=10",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_tickets_list_no_redirect_loop(http_client: httpx.AsyncClient, auth_headers: dict):
    props_r = await http_client.get("/api/v1/properties/", headers=auth_headers)
    prop_id = props_r.json()[0]["id"] if props_r.status_code == 200 and props_r.json() else None
    if not prop_id:
        pytest.skip("No property")
    r = await http_client.get(
        f"/api/v1/tickets/?property_id={prop_id}&limit=5",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_diagnostics_run(http_client: httpx.AsyncClient, auth_headers: dict):
    r = await http_client.get("/api/v1/system/diagnostics/run", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "summary" in data
    assert "checks" in data
    assert data["summary"]["total"] >= 4


@pytest.mark.asyncio
async def test_system_db_tables_super_admin(http_client: httpx.AsyncClient, auth_headers: dict):
    r = await http_client.get("/api/v1/system/db-tables", headers=auth_headers)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["table_count"] >= 1
    tables = payload["tables"]
    assert isinstance(tables, list)
    assert any(t.get("table_name") == "employees" for t in tables)
