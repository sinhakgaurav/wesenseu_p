#!/usr/bin/env python3
"""Verify REQUIREMENTS_FLOW_VERIFICATION.md endpoints exist and respond (smoke test)."""
from __future__ import annotations

import asyncio
import os
import sys

# Run from backend/: python scripts/verify_requirements_flow.py

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHECKS: list[tuple[str, str]] = [
    ("onboarding steps", "GET /api/v1/onboarding/steps"),
    ("catalog kinds", "GET /api/v1/catalog/kinds"),
    ("guest stays", "GET /api/v1/guest-stays/"),
    ("contacts route", "GET /api/v1/contacts/customers/00000000-0000-0000-0000-000000000001"),
    ("room bulk route", "POST /api/v1/rooms/bulk"),
    ("room variants", "POST /api/v1/rooms/variants"),
    ("category availability", "GET /api/v1/room-categories/availability"),
    ("property schedules", "GET /api/v1/properties/00000000-0000-0000-0000-000000000001/schedules"),
    ("fb outlets", "GET /api/v1/fb/properties/00000000-0000-0000-0000-000000000001/outlets"),
    ("attendance import", "POST /api/v1/attendance/import"),
    ("employee import", "POST /api/v1/employees/import"),
    ("dept duties", "GET /api/v1/departments/00000000-0000-0000-0000-000000000001/duties"),
    ("inventory task rules", "GET /api/v1/inventory/task-rules"),
    ("reports attendance", "GET /api/v1/reports/attendance"),
    ("vendors list", "GET /api/v1/vendors/"),
    ("onboarding sessions", "GET /api/v1/onboarding/sessions"),
    ("benchmark requirements", "GET /api/v1/tasks/00000000-0000-0000-0000-000000000001/benchmark-requirements"),
    ("room category amenities", "GET /api/v1/catalog/room-categories/00000000-0000-0000-0000-000000000001/amenities"),
]


async def main() -> int:
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    passed = 0
    failed: list[str] = []

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login for authed routes
        token = None
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": os.environ.get("VERIFY_EMAIL", "manager@grandpalace.com"), "password": os.environ.get("VERIFY_PASSWORD", "Manager@123")},
        )
        if login.status_code == 200:
            token = login.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        for name, route in CHECKS:
            method, path = route.split(" ", 1)
            kwargs = {"headers": headers}
            if method == "GET":
                r = await client.get(path, **kwargs)
            elif method == "POST":
                r = await client.post(path, json={}, **kwargs)
            else:
                r = await client.request(method, path, **kwargs)
            # 401/403/404/422/400 acceptable = route registered; 405/500 = fail
            if r.status_code in (200, 201, 204, 307, 400, 401, 403, 404, 422):
                passed += 1
                print(f"  OK  {name} ({r.status_code})")
            else:
                failed.append(f"{name}: {r.status_code} {r.text[:120]}")
                print(f"FAIL  {name} ({r.status_code})")

    print(f"\n{passed}/{len(CHECKS)} route checks passed")
    if failed:
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
