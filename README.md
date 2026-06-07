# Monitour — AI-Powered Operations & Workforce Management Platform

> Smart Operations, Surveillance & Workforce Management for Hotels, Hospitals & Facilities

---

## Overview

**Monitour** is a comprehensive, enterprise-grade SaaS platform for hospitality, healthcare, and facility management. It combines AI-based room verification, real-time CCTV surveillance, workforce management, room operations, ticketing, inventory tracking, pricing & plans, a CMS, an admin panel, and an AI customer support agent — all in one unified system.

---

## Architecture

```
React SPA (Vite + TypeScript)      http://localhost:3000
        ↓
FastAPI Backend (Python 3.13)      http://localhost:8000
        ↓                                    ↑ callback
  SQLAlchemy (async) + PostgreSQL    Celery → WesenseU AI (port 8001)
  Redis (task queue)
  S3 / local disk (file storage)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS, Redux Toolkit, React Query v5 |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x (async), Alembic |
| Database | PostgreSQL 16 (asyncpg) / SQLite (dev) |
| Cache/Queue | Redis 7 + Celery 5 |
| AI | WesenseU microservice (OpenCV, MediaPipe, DeepFace) |
| Storage | AWS S3 / Cloudflare R2 / MinIO / local disk |
| Deployment | Docker, Kubernetes, NGINX |

### Specification coverage

Maintain documentation **together with code** — see **[docs/DOCUMENTATION_POLICY.md](docs/DOCUMENTATION_POLICY.md)**.

| Doc | Use |
|-----|-----|
| [docs/README.md](docs/README.md) | Index of all spec/verification docs. |
| [docs/ARCHITECTURE_SPEC_CHECKLIST.md](docs/ARCHITECTURE_SPEC_CHECKLIST.md) | Stakeholder spec vs repo (**Implemented** / **Partial** / **Planned**) + §0 verification log. |
| [docs/FUNCTIONAL_DECISIONS_VERIFICATION.md](docs/FUNCTIONAL_DECISIONS_VERIFICATION.md) | Agreed features + WesenseU wiring (**Verified** / **Partial** / **Gap**). |
| [docs/SPEC_VS_REPO.md](docs/SPEC_VS_REPO.md) | Full PDF-style architecture vs this repository (honest deltas). |

---

## Quick Start

### Local Development (SQLite — no Postgres needed)

```bash
# Backend
cd Monitour/backend
pip install -r requirements.txt
python dev_start.py          # → http://localhost:8000/api/docs

# Frontend
cd Monitour/frontend
npm install
npm run dev                  # → http://localhost:3000
```

### With PostgreSQL

```bash
cd Monitour/backend
cp .env.example .env         # Configure DATABASE_URL, SECRET_KEY, etc.
python -m app.db.init_db     # Creates tables + seed data
uvicorn app.main:app --reload --port 8000
```

### Docker (Postgres + Redis + Monitour + WesenseU + Celery)

From the **Monitour** repo root, with the **WesenseU** repo cloned as a sibling folder (`../WesenseU/backend` must exist):

```bash
cd Monitour
docker compose up --build -d
```

| URL / port | Service |
|------------|---------|
| http://localhost:3000 | Monitour SPA (nginx; `/api/` proxied to Monitour API) |
| http://localhost:8000 | Monitour API (`/api/docs`) |
| http://localhost:8001 | WesenseU API (`/docs`) |
| localhost:5432 | Monitour Postgres |
| localhost:5433 | WesenseU Postgres |
| localhost:6379 | Monitour Redis |

On first start, the **backend** container runs `python -m app.db.init_db` (tables + demo seed), then **uvicorn**. A **Monitour Celery worker** and **WesenseU API + worker** run so room verification can flow end-to-end. Inside the stack, `WESENSEU_API_URL` is `http://wesenseu:8001/api/v1` and `MONITOUR_PUBLIC_URL` is `http://backend:8000` for service-to-service callbacks.

WesenseU services use **`WesenseU/backend/Dockerfile.compose`** and **`requirements-compose.txt`** (OpenCV + API stack only, no PyTorch/CUDA) so the first build stays reasonable. Full ML/video interview stack: build **`WesenseU/backend/Dockerfile`** with **`requirements.txt`** separately.

Apply Alembic migrations on an **existing** DB volume (after pulling new revisions):

```bash
docker compose exec backend alembic upgrade head
```

Stop and remove containers (keeps named volumes):

```bash
docker compose down
```

### Keep Docker databases *and* free host app ports (both)

Typical setup: **Postgres + Redis** (and WesenseU DB/Redis) stay in Docker, while you sometimes run **Monitour / WesenseU / Vite on the host** on ports 8000, 8001, 3000.

1. **Stop only app containers** (releases host ports 8000, 8001, 3000 from Docker):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/docker-stop-app-containers.ps1
   ```

2. **Kill stray host Python/Node** still holding those ports (does not touch Docker DB containers):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/clean-host-dev-ports.ps1
   ```

3. **Infra only** (no API containers) if you are not using the full stack yet:

   ```bash
   docker compose up -d db redis wesenseu_db wesenseu_redis
   ```

4. **Start the full Docker stack again** (APIs back in containers):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/docker-start-app-containers.ps1
   ```

---

## Default Login Credentials

Seed the database first: `python -m app.db.init_db` in the backend directory (or rely on the Docker backend startup command).

| Role | Email | Password | Access Level |
|------|-------|----------|-------------|
| Super Admin | admin@monitour.in | Admin@2026 | Full platform control |
| Property Manager | manager@grandpalace.com | Manager@123 | Property-level management |
| Dept Manager | hk_head@grandpalace.com | DeptHead@123 | Housekeeping department |
| Employee | priya@grandpalace.com | Password@123 | Task execution only |
| Customer | customer@grandpalace.com | Customer@123 | Customer portal |

All credentials are also shown on the **login page** as clickable quick-fill buttons.

---

## Features

### ✅ Core Platform
- JWT Authentication + RBAC (5 roles: super_admin, property_manager, dept_manager, employee, customer)
- Employee Management (CRUD, shifts, availability, **departments** — `/api/v1/departments` + **Admin → Departments**)
- Room Management (status lifecycle, QR codes, auto-task on checkout)
- Task Management (assignment, photo/video upload, AI verification workflow)
- Ticket Management (SLA tracking, guest portal, comments, routing)
- Inventory Management (stock tracking, IN/OUT transactions, low-stock alerts)
- Notification System (in-app, WebSocket real-time)
- Guest Portal (QR-based feedback and complaint submission)
- Admin Dashboard (live stats, charts, room visualization)

### ✅ Advanced Operations
- Orders / Room Service (full CRUD, status flow, revenue tracking)
- Attendance System (clock-in/out, monthly summary, history)
- Reports & Analytics (occupancy, tasks, tickets, revenue, departments)
- **AI Room Verification** — Celery downloads stored image URLs, POSTs **multipart** to WesenseU with **`room_category`** + optional **`benchmark_image_url`**, then callback updates Monitour
- **AI Benchmark Images** — Upload reference images per room category & aspect for AI comparison
- File Storage — S3/R2/MinIO with local disk fallback
- Celery Background Tasks (SLA breach alerts, low-stock emails, overdue escalation)
- Email Service (SMTP with console mock for development)

### ✅ Surveillance & Security
- **CCTV Camera Management** — Register IP/ONVIF cameras, WiFi discovery simulation
- **AI Surveillance Events** — WesenseU analyses clips/snapshots, creates `SurveillanceEvent` records
- Event severity tracking (low / medium / high / critical)
- AI monitoring toggle per camera

### ✅ Admin Panel
- Platform-wide statistics (properties, employees, open tasks)
- **Departments** — list / create / edit / deactivate under **Admin → Departments** (property managers; super admin picks property)
- **Property Approval Workflow** — Pending → Under Review → Approved/Rejected/Suspended
- **Module Configuration** — Enable/disable 12 feature modules per property
- Cross-property employee visibility

### ✅ Public / CMS
- **Pricing & Plans** — Full CRUD via admin, live fetch on public pricing page
- **Static Pages** — About Us, Contact, custom CMS pages with content blocks
- Landing Page, About, Contact public pages

### ✅ AI Customer Support
- Anonymous or authenticated support conversations
- Rule-based AI responses (pricing, features, CCTV, integrations, cancellation)
- Conversation status (open / resolved / escalated)
- Admin listing of all conversations

---

## API Documentation

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON (e.g. Postman **Import → Link**): `http://localhost:8000/openapi.json`
- Postman: import **`Monitour.postman_collection.json`** from the repository root (P0–P2 flows: Catalog, Onboarding, Contacts, F&B, Vendors, Guest Stays, Task SLA, and more). Flow/CRUD checklists: [docs/REQUIREMENTS_FLOW_VERIFICATION.md](docs/REQUIREMENTS_FLOW_VERIFICATION.md), [docs/CRUD_VERIFICATION.md](docs/CRUD_VERIFICATION.md). More detail: [docs/API_TOOLS.md](docs/API_TOOLS.md).

### Key Endpoints

| Service | Base Path |
|---------|-----------|
| Authentication | `/api/v1/auth` |
| Properties | `/api/v1/properties` |
| Employees | `/api/v1/employees` |
| Departments | `/api/v1/departments` |
| Rooms | `/api/v1/rooms` |
| Tasks | `/api/v1/tasks` |
| Verification | `/api/v1/verification` |
| Tickets | `/api/v1/tickets` |
| Inventory | `/api/v1/inventory` |
| Surveillance | `/api/v1/surveillance` |
| Benchmarks | `/api/v1/benchmarks` |
| Plans | `/api/v1/plans` |
| Pages | `/api/v1/pages` |
| Admin Panel | `/api/v1/admin` |
| Support Chat | `/api/v1/support` |
| Dashboard | `/api/v1/dashboard` |

---

## Project Structure

```
Monitour/
├── docker-compose.yml          # Postgres, Redis, Monitour + WesenseU + Celery workers
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI route handlers (20+ modules)
│   │   ├── core/               # Config, security (JWT, bcrypt)
│   │   ├── db/                 # Engine, session, seed
│   │   ├── models/             # SQLAlchemy ORM models (22 models)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Storage abstraction
│   │   └── worker/             # Celery tasks
│   ├── dev_start.py            # SQLite dev server (no Postgres needed)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI (Sidebar, Layout)
│   │   ├── pages/admin/        # 12 admin operation screens
│   │   ├── pages/public/       # Landing, About, Pricing, Contact, Support
│   │   ├── pages/super_admin/  # Admin Panel
│   │   ├── pages/guest/        # QR-based guest portal
│   │   ├── store/              # Redux (auth slice)
│   │   └── lib/                # API client (axios + interceptors)
│   └── Dockerfile
├── scripts/                    # Hybrid Docker + host dev helpers (see README Docker section)
│   ├── clean-host-dev-ports.ps1
│   ├── docker-stop-app-containers.ps1
│   └── docker-start-app-containers.ps1
├── Monitour.postman_collection.json
└── README.md
```

---

## Subscription Plans

| Plan | Rooms | Price/mo | Key Features |
|------|-------|----------|--------------|
| Starter | 10 | ₹4,000 | Core ops |
| Growth | 30 | ₹11,999 | + AI + CCTV |
| Enterprise | 50 | ₹20,000 | + Multi-prop + Admin |
| Custom | Unlimited | Custom | White-label + IoT |

---

## Environment Variables

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/monitour
REDIS_URL=redis://localhost:6379/0
WESENSEU_API_URL=http://localhost:8001/api/v1
WESENSEU_API_KEY=wesenseu-api-key-for-enterweu
MONITOUR_PUBLIC_URL=http://localhost:8000
STORAGE_BACKEND=local          # or "s3"
# WesenseU must reach MONITOUR_PUBLIC_URL for callbacks. Celery workers must HTTP GET
# verification image URLs when dispatching to WesenseU (use a public URL if services run in separate containers).
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

---

## Testing & logs

See [docs/TESTING.md](docs/TESTING.md). Quick run (stack must be up):

```powershell
powershell -File scripts/run-tests.ps1
```

Backend logs: `docker compose logs -f backend` (set `LOG_LEVEL=DEBUG` in `docker-compose.yml`).

---

## License

Proprietary. © 2026 Monitour Technologies Pvt. Ltd.
