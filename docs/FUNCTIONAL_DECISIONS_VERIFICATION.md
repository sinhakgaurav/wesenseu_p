# Monitour + WesenseU — Functional decisions verification

This document verifies **agreed product functionality** against the repositories.  
**Method:** static code audit (routers, workers, config, key UI routes) — 2026-05-14.

**Related:** [docs/README.md](./README.md) · [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) · [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md) · [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) (keep this file current when you change integrations or features).

**Status legend**

| Tag | Meaning |
|-----|---------|
| **Verified** | Code paths and APIs exist; primary flow is wired end-to-end in code. |
| **Partial** | Implemented but incomplete, optional path missing, or depends on external runtime (Redis/Celery/OpenCV). |
| **Gap** | Decision not met in code (fix or accept as out of scope). |

---

## A. Monitour ↔ WesenseU integration

| Decision | Status | Evidence |
|----------|--------|----------|
| Queue / async dispatch of room verification to WesenseU | **Verified** | `backend/app/worker/tasks.py` → `dispatch_to_wesenseu` → `POST {WESENSEU_API_URL}/rooms/verify`; triggered from `verification.py` via `.delay()`. |
| Callback to Monitour with AI result | **Verified** | WesenseU `worker/tasks.py` `_send_room_callback`; Monitour `verification` callback route (see `endpoints/verification.py`). |
| Configurable WesenseU base URL + API key | **Verified** | `app/core/config.py`: `WESENSEU_API_URL`, `WESENSEU_API_KEY`, `MONITOUR_PUBLIC_URL`. |
| Surveillance: Monitour submits media → WesenseU analyzes → callback | **Verified** | `surveillance.py` `POST /analyze` → WesenseU `POST /surveillance/analyze`; Monitour `POST /surveillance/callback`. |
| **Benchmark image** passed from Monitour to WesenseU on room verify | **Verified** | Celery `dispatch_to_wesenseu` resolves `RoomCategoryBenchmark` (prefer `aspect=general`) and sends `benchmark_image_url` + `room_category` on the WesenseU form. Staff photos are **downloaded** from stored URLs and posted as multipart `files` (WesenseU requires uploads). |

---

## B. Multi-property, RBAC, storage

| Decision | Status | Evidence |
|----------|--------|----------|
| Multiple properties + role-scoped users | **Verified** | `Property`, `Employee.role`, `property_id` scoping on endpoints; `super_admin` vs property roles. |
| Local filesystem storage (temporary / default) | **Verified** | `STORAGE_BACKEND` default `local` in `config.py`; `app/services/storage.py`. |
| Cloud storage option (S3/R2/MinIO) | **Verified** | Storage backend supports boto3-style backends per README/config. |

---

## C. REQ-style product modules (Monitour)

| Decision | Status | Evidence |
|----------|--------|----------|
| **N1** WesenseU image analysis with benchmarks | **Verified** | Benchmark CRUD + `dispatch_to_wesenseu` sends `benchmark_image_url`, `room_category`, and multipart image `files` (§A). |
| **N2** Monitour benchmark management per room category | **Verified** | `benchmarks` router + `RoomCategoryBenchmark` model + admin UI (`/admin/benchmarks`). |
| **N3** Video surveillance / events in Monitour | **Verified** | `surveillance` cameras/events + admin `SurveillancePage`. |
| **N4** CCTV WiFi discovery + add to system | **Verified** | `POST /surveillance/cameras/discover` (simulated) + camera CRUD. |
| **N5** CRUD coverage across modules | **Partial** | Broad CRUD present; **`/departments`** API + **`/admin/departments`** UI; not every sub-resource audited in this pass. |
| **N6** Admin: property approvals + per-property module flags | **Verified** | `super_admin.py`: `/admin/approvals*`, `/admin/modules/{property_id}/*`; `AdminPanelPage`. |
| **N7** Pricing / plans DB + admin + public | **Verified** | `Plan` model, `/plans`, `PricingPage`, seeding in lifespan/`init_db`. |
| **N8** Static pages CMS | **Verified** | `/pages`, admin publish flows (`pages` router). |
| **N9** AI customer support | **Verified** | `/support` + `SupportChatWidget` global. |

---

## D. Later operational features (Monitour)

| Decision | Status | Evidence |
|----------|--------|----------|
| Hotel surveillance **scenario checklist** | **Verified** | `app/constants/surveillance_hotel_scenarios.py` + `GET /surveillance/hotel-surveillance-scenarios`. |
| **Timer-based** surveillance event recording | **Partial** | `POST /surveillance/timer-events` + event fields; **automatic** stream timers = WesenseU/edge **Partial**. |
| **Laundry** management | **Verified** | `LaundryOrder`, `/laundry`, `/admin/laundry`. |
| **Task SLA** by task type + service type + RCA bucket | **Verified** | `TaskSlaPolicy`, `/task-sla-policies`, task `sla_due_at` / breach fields, `task_sla.py`. |
| **Auto-assign** to longest-idle free employee | **Verified** | `POST /tasks/{task_id}/auto-assign`, `task_assignment.py`, create flag `auto_assign`. |
| **Guest** check-in / check-out | **Verified** | `GET /rooms/guest-stays`, `POST /rooms/{id}/guest-check-in`, checkout; `/admin/guests`. |

---

## E. WesenseU service (companion repo)

| Decision | Status | Evidence |
|----------|--------|----------|
| Room verification job + callback | **Verified** | `WesenseU/.../endpoints/rooms.py`, worker `_send_room_callback`. |
| Surveillance job + callback to Monitour | **Verified** | `surveillance.py`, `analyze_surveillance` task, callback POST. |
| Analysis implementation (OpenCV / mocks) | **Partial** | `surveillance_analyzer.py` may mock if OpenCV missing. |

---

## F. Frontend (admin + public)

| Area | Status | Evidence |
|------|--------|----------|
| Admin sidebar: core ops + benchmarks, surveillance, laundry, guests, **departments** | **Verified** | `Sidebar.tsx` nav items; `/admin/departments` → `DepartmentsPage.tsx`. |
| Public marketing + pricing + support page | **Verified** | `App.tsx` routes; `PricingPage`, `SupportChatPage`. |
| Floating support widget | **Verified** | `SupportChatWidget` in `App.tsx`. |
| Guest QR portal | **Verified** | `/guest/:roomId` → `GuestPortalPage`. |

---

## G. Dev experience & tests

| Decision | Status | Evidence |
|----------|--------|----------|
| SQLite-friendly dev start | **Verified** | `backend/dev_start.py` type patch + `README` quick start. |
| Cross-service / integration tests (workspace) | **Partial** | Test suite at `e:/projects/tests/` (Monitour + WesenseU integration, e2e verification flow, cross_service). **Runtime proof** requires running pytest with services up (see `tests/run_tests.ps1` / project docs). |

---

## H. Consolidated action list (from this verification)

1. **Re-run verification** after each release: reload app routes + grep for removed `include_router` entries; update this file’s date and table — per [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md).

---

*Companion docs: [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md) (stakeholder spec vs repo) · [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) (architecture document vs code) · [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) (maintenance rules).*
