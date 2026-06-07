"""Shared pytest fixtures for Monitour API tests."""
from __future__ import annotations

import os

import httpx
import pytest

API_BASE = os.environ.get("MONITOUR_API_URL", "http://localhost:8000").rstrip("/")
DEMO_EMAIL = os.environ.get("MONITOUR_DEMO_EMAIL", "admin@monitour.in")
DEMO_PASSWORD = os.environ.get("MONITOUR_DEMO_PASSWORD", "Admin@2026")


@pytest.fixture(scope="session")
def api_base() -> str:
    return API_BASE


@pytest.fixture
async def http_client(api_base: str):
    async with httpx.AsyncClient(base_url=api_base, timeout=30.0, follow_redirects=True) as client:
        yield client


@pytest.fixture
async def auth_headers(http_client: httpx.AsyncClient) -> dict[str, str]:
    r = await http_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
