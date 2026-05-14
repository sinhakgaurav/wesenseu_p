# Technical architecture document vs Monitour repository

This document compares the **written technical architecture** (multi-tenant SaaS, Kafka EDA, microservices, full data model) to the **current Monitour codebase** under `backend/app` and `frontend/`. It is the single place for **architectural honesty**; keep it updated per [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md).

**Last reviewed:** 2026-05-14 (departments API + WesenseU multipart/benchmark dispatch).  

---

## Legend

| Status | Meaning |
|--------|---------|
| **Implemented** | Matches intent in code (naming may differ). |
| **Partial** | Subset, stub, or different pattern than the document. |
| **Not implemented** | Not present in application code. |
| **Different** | Same goal, different mechanism (call out explicitly). |

---

## 1. System architecture (document §3–5)

| Document claim | Status | Notes |
|----------------|--------|-------|
| Hybrid microservices (separate Auth, User, Property, Task, … deployables) | **Different** | **Modular monolith:** one FastAPI app, routers as module boundaries. |
| Apache Kafka as backbone + listed topics | **Not implemented** | No Kafka producer/consumer in `backend/app`. |
| Event flow: room.checkout → Kafka → … → WesenseU | **Different** | **Celery + HTTP** to WesenseU; **HTTP callback** to Monitour for verification/surveillance. |
| Queue orchestrator service | **Different** | **Celery** + Redis (when configured). |
| “EDA” at platform level | **Partial** | Async work via tasks, DB state, notifications — not Kafka-style event bus. |

---

## 2. Technology stack (document §4)

| Component | Document | Repo |
|-----------|----------|------|
| API | FastAPI | **Implemented** |
| ORM | SQLAlchemy | **Implemented** (async) |
| Auth | JWT + OAuth2 | **Implemented** — OAuth2 **password** bearer + refresh; not full social OAuth2 suite in app. |
| Workers | Celery | **Implemented** |
| Kafka | Yes | **Not implemented** (app) |
| DB | PostgreSQL | **Implemented** (typical); SQLite dev path exists. |
| Cache | Redis | **Partial** — broker/cache as deployment concern. |
| Object storage | S3 | **Partial** — configurable; default local. |
| Search | Elasticsearch | **Not implemented** |
| Realtime | Socket.IO | **Different** — **FastAPI WebSocket** (`/api/v1/notifications/ws/{user_id}`). |
| Web app | React Native PWA | **Different** — **React + Vite SPA**. |
| Admin UI | React + Material UI | **Different** — **Tailwind + lucide** (+ Redux Toolkit, React Query). |

---

## 3. Multi-tenant & hierarchy (document §6, §9)

| Document | Status | Notes |
|----------|--------|-------|
| `tenant_id` on entities | **Different** | Scoping via **`property_id`**, **`customer_id`** (B2B customer). |
| `companies` table | **Different** | **`customers`** with `company_name`; properties link to customer. |
| Company → Property → Building → Floor → Room | **Partial** | Property → Room; **`floor_number`** on room; **no Building/Floor tables**. |
| `room_categories` table + FK | **Partial** | **`room_category` string** on `Room`; benchmarks key off string + `RoomCategoryBenchmark`. |
| `departments` + REST CRUD | **Implemented** | `/api/v1/departments` (list/create/get/patch/soft-delete). |
| `users` / `roles` / `permissions` tables | **Different** | Staff = **`employees`** with string **`role`**; no ACL permission matrix. |

---

## 4. Functional modules (document §7)

| Module | Status | Notes |
|--------|--------|-------|
| Employee CRUD, attendance, shifts metadata | **Implemented** | `employees`, `attendance`. |
| Smart / longest-idle assignment | **Implemented** | `tasks` auto-assign. |
| Room lifecycle, guest/QR | **Implemented** | `rooms`. |
| Benchmark images per category/section | **Partial** | `room_category_benchmarks` + `aspect`; no `validation_threshold` as in doc table. |
| AI verification workflow | **Implemented** | `RoomVerification` + WesenseU dispatch/callback. |
| Benchmark URL passed to WesenseU on verify | **Implemented** | `dispatch_to_wesenseu` resolves benchmark URL, sends `benchmark_image_url` + `room_category`; staff images POSTed as multipart `files`. |
| Tickets, inventory, surveillance, laundry | **Implemented** | Routers in `api/v1/router.py`. |
| Task SLA policies + breach handling | **Implemented** | `task_sla_policies`, workers, task fields. |
| Surveillance timers / hotel scenarios | **Partial** | APIs + scenarios; full autonomous CCTV pipeline not in scope of this repo alone. |
| Notifications: push / SMS / email / WhatsApp | **Partial** | Model + WebSocket; **SMTP** helper; no Twilio/WhatsApp in `app/`. |
| Billing / subscription / invoicing | **Partial** | `Plan`, subscription fields on customer/property; no Stripe/invoice engine in code. |
| AI support agent | **Implemented** | `support`. |
| CMS pages + pricing | **Implemented** | `pages`, `plans`. |
| Super admin approvals + module toggles | **Implemented** | `admin` (`super_admin`). |

---

## 5. Database tables (document §8–9) — name mapping

| Document table | Monitour (approx.) |
|----------------|-------------------|
| `companies` | `customers` (+ `company_name`) |
| `properties` | `properties` |
| `departments` | `departments` |
| `users` | `employees` (staff); guest flows separate |
| `roles` / `permissions` | **Not separate tables** — `Employee.role` |
| `rooms` | `rooms` |
| `room_categories` | **String on `rooms`** + benchmarks |
| `benchmark_images` | `room_category_benchmarks` |
| `tasks` | `tasks` |
| `task_logs` | **Not present** — use task status / `RoomAuditLog` / media as applicable |
| `tickets` | `tickets` |
| `inventory_*` | `inventory_items`, `inventory_transactions`, `vendors` |
| `cctv_devices` | `surveillance_cameras` (conceptual match) |
| `surveillance_events` | `surveillance_events` |
| `image_validation_results` | **Fields on `room_verifications`** |
| `notifications` | `notifications` |
| `laundry_requests` | `laundry_orders` |
| Soft delete (`deleted_at`) everywhere | **Not implemented** as cross-cutting pattern |
| Universal `created_by` / `updated_by` | **Partial** |

---

## 6. WesenseU integration (document §13)

| Document | Repo |
|----------|------|
| Monitour → Kafka → WesenseU | **Different** — **HTTP multipart** from Celery (downloaded image bytes); WesenseU **POST callback** to Monitour. |
| Room image analysis | **Implemented** |
| Surveillance analysis | **Implemented** |
| Benchmark comparison in WesenseU | **Implemented** | Monitour supplies URL + files; WesenseU pipeline compares when OpenCV available. |

---

## 7. Security, observability, deployment (document §17–19)

| Item | Status |
|------|--------|
| MFA | **Not implemented** in app code |
| HTTPS / at-rest encryption | **Deployment** |
| Prometheus, Grafana, ELK, Vault, K8s service matrix | **Not described in application code** |

---

## 8. Related documents

- [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md) — line-by-line checklist + §0 verification log.  
- [FUNCTIONAL_DECISIONS_VERIFICATION.md](./FUNCTIONAL_DECISIONS_VERIFICATION.md) — integration and feature matrix.  
- [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) — **always update after implementation**.
