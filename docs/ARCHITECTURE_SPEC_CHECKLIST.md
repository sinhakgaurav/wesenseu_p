# Monitour — Architecture & UI Specification Checklist

This document maps the **Technical Architecture, Database Design & UI Specification** (target blueprint) to the **current Monitour repository**. Use it for gap analysis and roadmap planning.

**Related:** [docs/README.md](./README.md) (index) · [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) (architecture doc vs code) · [FUNCTIONAL_DECISIONS_VERIFICATION.md](./FUNCTIONAL_DECISIONS_VERIFICATION.md) (integration matrix) · [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) (**update docs after every implementation**).

**Status legend**

| Status | Meaning |
|--------|---------|
| **Implemented** | Delivered in this repo; primary user path works. |
| **Partial** | Present but limited, stubbed, differs from spec naming, or needs integration hardening. |
| **Planned** | Not in repo; future / optional per original spec. |

---

## 0. Verification log (repository audit)

This section records **follow-up verification** of checklist claims against the Monitour repo (static audit: OpenAPI routes, router registration, frontend routes). Re-run after major merges.

**Last verified:** 2026-05-20 (CRUD + admin UI completion pass).

| # | Verification task | Result | Evidence / method |
|---|-------------------|--------|-------------------|
| V1 | FastAPI application imports and exposes routes | **Pass** | `python scripts/verify_requirements_flow.py` |
| V12 | Vendors CRUD API | **Pass** | `/api/v1/vendors` |
| V13 | Catalog item PATCH/DELETE | **Pass** | `/api/v1/catalog/items/{id}` |
| V14 | Contacts PATCH | **Pass** | `/api/v1/contacts/properties/{id}/{contact_id}` |
| V15 | F&B outlet/menu U/D | **Pass** | `/api/v1/fb/outlets`, `/fb/menu/{id}` |
| V16 | Onboarding sessions list | **Pass** | `GET /api/v1/onboarding/sessions` |
| V17 | Admin UI: property settings, F&B, SLA, properties | **Pass** | `PropertySettingsPage`, `FnBPage`, `TaskSlaPage`, `PropertiesPage` |
| V18 | P2 sample seeder | **Pass** | `app/db/seed_p2_sample.py` via `init_db` |
| V19 | CRUD matrix doc | **Pass** | `docs/CRUD_VERIFICATION.md` |
| V2 | Auth: login, refresh, logout | **Pass** | `/api/v1/auth/login`, `/auth/refresh-token`, `/auth/logout` present |
| V3 | Auth: forgot-password | **Fail (expected)** | No route in `auth.py`; matches **Planned** row in §5 |
| V4 | Core domain routers registered | **Pass** | `router.py` includes `rooms`, `tasks`, `tickets`, `inventory`, `attendance`, `verification`, `surveillance`, `laundry`, `task_sla_policies`, `support`, `plans`, `pages`, … |
| V5 | Guest stay & laundry APIs | **Pass** | `/api/v1/rooms/guest-stays`, `/rooms/{id}/guest-check-in`, `/rooms/{id}/checkout`, `/api/v1/laundry`, `/laundry/{order_id}` |
| V6 | Task SLA + auto-assign | **Pass** | `/api/v1/task-sla-policies`, `/tasks/{task_id}/auto-assign` |
| V7 | Surveillance checklist + timer event | **Pass** | `/api/v1/surveillance/hotel-surveillance-scenarios`, `/surveillance/timer-events`, cameras/events/analyze/callback |
| V8 | WebSocket notifications endpoint | **Pass** | `/api/v1/notifications/ws/{user_id}` (client subscription coverage remains **Partial** per §9) |
| V9 | Admin SPA routes for new modules | **Pass** | `App.tsx`: `/admin/guests`, `/admin/laundry`, `/admin/surveillance`, `/admin/departments`, … |
| V10 | Dedicated departments CRUD API | **Pass** | `GET/POST/PATCH/DELETE /api/v1/departments` (`endpoints/departments.py`); super_admin lists with `?property_id=`; admin UI `DepartmentsPage.tsx` |
| V11 | Admin Departments management UI | **Pass** | `Sidebar.tsx` link; `DepartmentsPage.tsx` (list/create/edit/deactivate); property picker for `super_admin` |

**Follow-up actions (from this audit)**

1. **Forgot password:** Implement `POST /auth/forgot-password` + token flow or remove UI placeholder.  
2. **WebSocket:** Wire admin SPA to `/notifications/ws/{user_id}` if real-time in-app alerts are required.  
3. Re-run rows V1–V11 before each release candidate.

---

## 1. Technical overview & stack

| Requirement | Status | Notes |
|-------------|--------|-------|
| Product: Monitour (AI-assisted ops & workforce) | **Implemented** | Core positioning matches. |
| Target: Hotels | **Implemented** | Primary flows (rooms, guests, housekeeping). |
| Target: Hospitals | **Partial** | Generic facility models; not hospital-specific UX/workflows. |
| Target: Resorts, guest houses, facility mgmt, chains | **Partial** | Multi-property + RBAC; industry-specific templates **Planned**. |
| Frontend: React + TypeScript | **Implemented** | Vite SPA under `frontend/`. |
| Frontend: React Native | **Planned** | Spec mobile app; repo is **web only**. |
| Redux Toolkit | **Implemented** | `frontend/src/store`. |
| React Query | **Implemented** | Data fetching across admin pages. |
| Tailwind (spec also mentions NativeWind) | **Implemented** | Tailwind; no React Native → no NativeWind. |
| PWA | **Partial** | Not configured as installable PWA by default. |
| WebSocket integration | **Partial** | `GET` notifications REST + `WebSocket` `/api/v1/notifications/ws/{user_id}`; client wiring may be incomplete. |
| Backend: Python + FastAPI | **Implemented** | `backend/app`. |
| Backend: Django Admin (optional) | **Planned** | Not used; super-admin is custom FastAPI + React. |
| Celery + Redis | **Partial** | Present for workers; local dev often SQLite without full broker. |
| PostgreSQL | **Implemented** | Production path; asyncpg. |
| SQLAlchemy async | **Implemented** | |
| Alembic | **Partial** | Present under `backend/alembic`; dev often `create_all` / SQLite. |
| Docker | **Partial** | Compose/docs vary; not the only run path. |
| Kubernetes / cloud / NGINX / CDN | **Planned** | Deployment guidance; not codified as manifests in this checklist scope. |
| S3-compatible object storage | **Implemented** | Configurable local + boto3 S3/R2/MinIO. |
| WesenseU integration APIs | **Implemented** | Verification + surveillance analyze/callback. |
| OpenCV / AI event detection (WesenseU) | **Partial** | Integrated; depth depends on WesenseU build (mock vs real). |
| YOLO (future surveillance) | **Planned** | Spec “future”; not required in Monitour core repo. |

---

## 2. High-level architecture components

| Component (spec) | Status | Notes |
|------------------|--------|-------|
| Frontend applications | **Implemented** | Admin web + public marketing + guest QR portal. |
| API gateway (dedicated) | **Partial** | FastAPI app acts as API; no separate Kong-style gateway. |
| Authentication service | **Implemented** | `/api/v1/auth` (JWT, refresh). |
| Employee management | **Implemented** | Employees, **departments CRUD** (`/departments`), attendance endpoints. |
| Room management | **Implemented** | Rooms, status, audit, guest check-in/out, guest-stays list. |
| Inventory service | **Implemented** | CRUD + transactions. |
| Ticketing service | **Implemented** | Tickets + guest QR path. |
| Task management | **Implemented** | Tasks, media, SLA policies, auto-assign longest-idle. |
| Reporting service | **Implemented** | Reports endpoints + dashboards (scope varies). |
| Notification service | **Partial** | Model + REST + WebSocket stub; push/SMS/email senders not full product. |
| Surveillance service | **Partial** | Cameras, events, scenarios checklist, timer-event API; live CV pipeline **Partial**. |
| AI verification service | **Implemented** | WesenseU + Monitour verification flow. |
| Media upload service | **Implemented** | Storage abstraction + upload endpoints. |
| Billing & subscription | **Partial** | Plans model, pricing page, admin seeds; full billing provider **Planned**. |
| Database layer | **Implemented** | SQLAlchemy models. |
| Cache layer | **Partial** | Redis used with Celery; not universal app cache layer. |
| Object storage layer | **Implemented** | |
| Analytics engine | **Partial** | Reporting/dashboards; not separate warehouse. |

---

## 3. End-to-end workflow (example: housekeeping verification)

| Step (spec) | Status | Notes |
|-------------|--------|-------|
| Guest checkout → room status updated | **Implemented** | `POST /rooms/{id}/checkout`. |
| Task auto-created | **Implemented** | Cleaning task on checkout / status paths. |
| Employee assigned | **Implemented** | Manual, `auto_assign`, or `POST .../auto-assign`. |
| Employee uploads photos/videos | **Implemented** | Task media upload. |
| Media storage | **Implemented** | |
| WesenseU verification API | **Implemented** | Queue + callback patterns. |
| AI validation → task status | **Implemented** | Verification pending → approve/reject. |
| Manager notification | **Partial** | Notifications created; channel delivery **Partial**. |
| Room ready status | **Implemented** | On approved cleaning task. |
| Reports & analytics updated | **Partial** | Depends on reporting usage. |

---

## 4. Frontend applications (spec)

| Application | Status | Notes |
|---------------|--------|-------|
| Admin dashboard (web) | **Implemented** | `/admin/*`. |
| Employee mobile app | **Planned** | Spec React Native; **web** responsive admin/employee use only. |
| Guest web portal (QR) | **Implemented** | Guest portal route + QR room access patterns. |
| Property selector on login (spec screen) | **Partial** | Multi-property via user context; dedicated login property picker **Partial** / **Planned**. |

---

## 5. Backend “microservices” (spec vs repo)

Spec lists separate service folders. **Monitour uses a modular monolith** (`app/api/v1/endpoints/*`).

| Spec service / capability | Status | Monitour mapping |
|---------------------------|--------|------------------|
| Auth: login / logout / refresh | **Implemented** | `/auth/login`, `/auth/logout`, `/auth/refresh-token`. |
| Auth: forgot-password | **Planned** | UI placeholder; endpoint not in checklist audit. |
| Employee CRUD | **Implemented** | `/employees`. |
| Departments | **Implemented** | `Department` model + `GET/POST/PATCH/DELETE /api/v1/departments` + reporting (`GET /api/v1/reports/departments`) + **admin UI** `/admin/departments`. |
| Attendance | **Implemented** | `/attendance`. |
| Salary / shift (spec breadth) | **Partial** | Shift + salary fields on employee; full payroll **Planned**. |
| Rooms / status / audit | **Implemented** | `/rooms`, audit logs, guest flows. |
| Room verification | **Implemented** | `/verification`. |
| Tasks / status / SLA | **Implemented** | `/tasks`, `/task-sla-policies`, auto-assign. |
| Laundry | **Implemented** | `/laundry`, admin UI. |
| Ticketing + comments | **Implemented** | `/tickets`. |
| Inventory / vendors | **Implemented** | Inventory + vendor models. |
| Notifications / broadcast | **Partial** | CRUD + WS; broadcast to devices **Partial**. |
| Reports / analytics / dashboard | **Partial** | Endpoints exist; depth vs spec dashboards **Partial**. |
| Surveillance cameras / events / alerts | **Partial** | See surveillance section. |
| CMS pages | **Implemented** | `/pages` + admin. |
| Support AI chat | **Implemented** | `/support` + widget. |

---

## 6. Database design (spec tables vs repo)

| Spec table / area | Status | Notes |
|-------------------|--------|-------|
| `properties` | **Implemented** | |
| `departments` | **Implemented** | |
| `employees` | **Implemented** | RBAC roles. |
| `rooms` (+ guest fields, `expected_check_out`) | **Implemented** | Extended beyond original spec snippet. |
| `tasks` (+ `service_type`, SLA columns) | **Implemented** | Extended. |
| `task_sla_policies` | **Implemented** | Not in original spec table list; added for SLA/RCA. |
| `task_media` | **Implemented** | |
| `room_verifications` | **Implemented** | |
| `inventory_items` / transactions / vendors | **Implemented** | |
| `tickets` / comments | **Implemented** | |
| `orders` | **Implemented** | |
| `feedback` | **Implemented** | |
| `notifications` | **Implemented** | |
| `surveillance_cameras` (+ `scenario_rules`) | **Implemented** | Extended. |
| `surveillance_events` (+ timer/scenario fields) | **Implemented** | Extended vs spec snippet. |
| `laundry_orders` | **Implemented** | Not in original spec list. |
| `plans`, `pages`, approvals, module_config, customers, benchmarks, support` | **Implemented** | Beyond minimal spec. |

---

## 7. Surveillance (spec section + your checklist)

| Requirement | Status | Notes |
|-------------|--------|-------|
| CCTV mapping / cameras | **Implemented** | CRUD + discover stub. |
| Event detection & dashboard | **Partial** | Events list + severities; live detection = WesenseU + callbacks. |
| Hotel unwanted-scenario checklist | **Implemented** | Constants + `GET .../hotel-surveillance-scenarios`. |
| Timer-based events (e.g. guard > 3 min) | **Partial** | `POST .../timer-events` + metadata on events; **automatic** timer on stream **Planned** / WesenseU. |
| Security alerts to managers | **Partial** | Notifications for high/critical paths; full paging **Partial**. |

---

## 8. Authentication & RBAC (spec roles)

| Role / capability | Status | Notes |
|-------------------|--------|-------|
| Super admin | **Implemented** | |
| Property manager | **Implemented** | |
| Department manager | **Implemented** | |
| Employee | **Implemented** | |
| Customer / guest portal | **Partial** | Guest flows; dedicated “customer” product role **Partial**. |
| Guest (QR) | **Implemented** | Ticket/feedback patterns. |
| Fine-grained permission matrix (per spec prose) | **Partial** | Role-based; not full ABAC policy engine. |

---

## 9. Notification architecture (spec)

| Channel / feature | Status | Notes |
|-------------------|--------|-------|
| In-app / DB notifications | **Implemented** | |
| WebSocket | **Partial** | Server endpoint exists; universal client subscription **Partial**. |
| Push (FCM) | **Planned** | Metadata only unless wired. |
| Email | **Planned** | |
| SMS / WhatsApp | **Planned** | |

---

## 10. Media storage (spec)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Room / verification / CCTV uploads | **Implemented** | |
| Compression / virus scan pipeline | **Planned** | Spec flow; not default in repo. |

---

## 11. Sample screens (spec)

| Screen | Status | Notes |
|--------|--------|-------|
| Login | **Implemented** | |
| Manager dashboard | **Implemented** | Widgets differ from ASCII mock; same intent. |
| Employee task screen | **Partial** | Web tasks UI; not native mobile layout. |
| Ticket management | **Implemented** | |
| AI verification | **Implemented** | Flow via verification + tasks. |
| Surveillance monitoring | **Implemented** | + scenario checklist section. |
| Laundry / guest stays | **Implemented** | Beyond original spec list. |

---

## 12. Deployment & scalability (spec)

| Topic | Status | Notes |
|-------|--------|-------|
| Stateless API design | **Partial** | Suitable for horizontal scale; WS sticky sessions caveat. |
| K8s autoscaling / CDN / queue at scale | **Planned** | Ops patterns. |
| RabbitMQ / Kafka | **Planned** | Celery+Redis today. |

---

## 13. Future enhancements (spec Phase / “planned features”)

| Feature | Status | Notes |
|---------|--------|-------|
| Face recognition attendance | **Planned** | |
| Smart occupancy | **Partial** | Room occupancy fields; not IoT depth. |
| Voice assistant | **Planned** | |
| IoT / smart locks | **Planned** | |
| Predictive maintenance / AI staffing / energy | **Planned** | |

---

## 14. Development phases (spec)

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Auth, employees, rooms, tickets, tasks | **Implemented** | |
| Phase 2 — AI verification, inventory, notifications, reporting | **Partial** | Mostly present; channel depth **Partial**. |
| Phase 3 — Surveillance integration, CCTV AI, predictive analytics | **Partial** | Integrated stack; predictive **Planned**. |
| Phase 4 — IoT, smart property ecosystem | **Planned** | |

---

## 15. How to update this checklist

0. Follow **[DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md)** — update this file, [SPEC_VS_REPO.md](./SPEC_VS_REPO.md), and [FUNCTIONAL_DECISIONS_VERIFICATION.md](./FUNCTIONAL_DECISIONS_VERIFICATION.md) in the **same change set** as the code when behavior or APIs change.  
1. After each release, adjust **Status** and **Notes** to match `main`.  
2. Prefer **Partial** over **Implemented** when only stubs or happy-path exists.  
3. Link implementation details to `README.md` and `/api/docs` for API truth.  
4. Update **§0 Verification log** (date, table, follow-up actions) whenever you re-run the audit commands below.

### Quick re-verification commands (from `Monitour/backend`)

```bash
# App loads
python -c "import dev_start; from app.main import app; print('routes', len(app.routes))"

# Sample critical paths (PowerShell)
# Invoke-RestMethod http://localhost:8000/openapi.json | ConvertFrom-Json | % paths
```

---

*Generated for Monitour repository traceability. Spec source: stakeholder “Technical Architecture, Database Design & UI Specification” document.*
