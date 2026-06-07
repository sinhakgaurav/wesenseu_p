# Testing & logging

## Logging

Backend request logging is enabled via `LOG_LEVEL` (default `INFO`, Docker uses `DEBUG`).

- Config: `backend/app/core/logging_config.py`
- HTTP middleware: `backend/app/middleware/request_logging.py`
- Each request logs `→ METHOD path [id]` and `← METHOD path [id] STATUS ms`
- Response header: `X-Request-ID`

View logs:

```bash
docker compose logs -f backend
```

## Backend integration tests (pytest)

Requires the API running (`docker compose up`).

```bash
docker compose exec -T backend pip install -r requirements-dev.txt
docker compose exec -T backend pytest tests/ -v
```

Or run everything:

```powershell
powershell -File scripts/run-tests.ps1
```

Environment overrides:

| Variable | Default |
|----------|---------|
| `MONITOUR_API_URL` | `http://localhost:8000` |
| `MONITOUR_DEMO_EMAIL` | `admin@monitour.in` |
| `MONITOUR_DEMO_PASSWORD` | `Admin@2026` |

## Frontend unit tests (Vitest)

```bash
cd frontend
npm install
npm run test
```

## Frontend E2E (Playwright)

Requires frontend at `http://localhost:3000` and backend at `http://localhost:8000`.

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

Optional: `PLAYWRIGHT_BASE_URL`, `PLAYWRIGHT_DEMO_EMAIL`, `PLAYWRIGHT_DEMO_PASSWORD`.

## Diagnostics console (UI)

Super Admin → **Admin Panel** → **Diagnostics** tab runs probes for:

- PostgreSQL, Redis, Celery broker, WesenseU
- Each API module (auth, tickets, tasks, rooms, …)

API: `GET /api/v1/system/diagnostics/run` (super_admin only).

After frontend changes, rebuild the UI container:

```bash
docker compose up -d --build frontend backend
```
