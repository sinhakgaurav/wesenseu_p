# Requirements flow verification & roadmap

**Purpose:** Single source of truth for product flows vs the Monitour repository.

**Last updated:** 2026-05-20 (CRUD + admin UI completion pass)

---

## Admin UI coverage (2026-05-20)

| Module | Admin route | Status |
|--------|-------------|--------|
| Property settings (contacts, hours) | `/admin/property-settings` | **Done** |
| F&B outlets & menu | `/admin/fnb` | **Done** |
| Task SLA policies | `/admin/task-sla` | **Done** |
| Properties (super_admin) | `/admin/properties` | **Done** |
| Departments (manager + duties) | `/admin/departments` | **Done** |
| Room categories (amenities + pool) | `/admin/room-categories` | **Done** |
| Inventory (edit/photo/delete) | `/admin/inventory` | **Done** |
| Tasks (media + WesenseU) | `/admin/tasks` | **Done** |

Full matrix: **`docs/CRUD_VERIFICATION.md`**

---

## Status legend

| Tag | Meaning |
|-----|---------|
| **Done** | Implemented (API + model and/or UI). |
| **Partial** | Works but differs from original spec naming or depth. |
| **Out of scope** | Explicitly not in repo (Kafka microservices, React Native, K8s manifests). |

---

## Summary (2026-05-20)

| Section | Done | Partial | Out of scope |
|---------|------|---------|--------------|
| §1 Onboarding | 6 | 2 | 0 |
| §2 Employees | 4 | 1 | 0 |
| §3 Property ops | 5 | 1 | 0 |
| §4 Tasks | 3 | 0 | 0 |
| §5 Tickets/billing | 3 | 0 | 0 |
| §6 Reporting | 2 | 0 | 0 |

**Automated smoke test:** `docker compose exec backend python scripts/verify_requirements_flow.py`

---

## Flow verification matrix

### §1 Onboarding

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 1.1 | Business multi-contact | **Done** | `/contacts/customers/{id}`; wizard step |
| 1.2 | Multi-step wizard | **Done** | `/onboarding/sessions` + `/admin/onboarding` |
| 1.2.a | Property type, features | **Done** | Catalog + `PUT /catalog/properties/{id}/features` |
| 1.2.b | Property contacts | **Done** | `/contacts/properties/{id}` |
| 1.2.c | Room types, amenities, benchmarks | **Done** | Room categories, catalog amenities, benchmarks |
| 1.2.d | Bulk rooms / variants | **Done** | `POST /rooms/bulk`, `POST /rooms/variants`, `room_variants` |
| 1.2.e | F&B outlets, menu, dishes | **Done** | `/fb/properties/{id}/outlets`, menu items; `dish` catalog |
| 1.2.f | Inventory with photos | **Done** | `POST /inventory/items/{id}/photo` |

### §2 Employee management

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 2.1 | Departments + duty catalog M:N | **Done** | `PUT /departments/{id}/duties` |
| 2.1 | Bulk CSV import | **Done** | `POST /employees/import` |
| 2.2 | Leave / lunch / weekly off | **Done** | `POST /attendance/records`, `PUT /attendance/employees/{id}/schedule`; assignment skips |
| 2.2 | Manager attendance import | **Done** | `POST /attendance/import` |
| 2.3 | Dept manager notifications | **Done** | `notify_managers` on tickets/tasks; notifications API |

### §3 Property management

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 3.1 | Check-in / check-out | **Done** | `guest_stays` |
| 3.2.a | Checkout → cleaning task | **Done** | |
| 3.2.b | Auto-assign longest-idle | **Done** | Skips leave, weekly off, lunch |
| 3.2.c | Mandatory benchmark photos | **Done** | `benchmark_requirements` service |
| 3.2.d | WesenseU + notify | **Partial** | Celery HTTP + in-app notifications (not Kafka) |
| 3.2.e | Category availability pool | **Done** | `GET /room-categories/availability` |

### §4 Task management

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 4.1.a | Smart assign | **Done** | |
| 4.1.b | Inventory on complete | **Done** | `task_inventory_rules` + auto OUT on complete/approved |
| 4.1.c | Last completion time | **Done** | |

### §5 Tickets & guest billing

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 5.1 | QR → department routing | **Done** | |
| 5.2 | Ticket → task | **Done** | |
| 5.x | Stay-scoped folio | **Done** | `guest_stay_id` on orders/tickets |

### §6 Reporting

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| 6.1 | Department breakdown | **Done** | Tasks joined via `Employee.department_id` |
| 6.2 | Leave/break report | **Done** | `GET /reports/attendance` |

---

## Property schedules (P1)

| Item | Status | Notes |
|------|--------|-------|
| Operating hours per day | **Done** | `GET/PUT /properties/{id}/schedules` |

---

## Architecture (unchanged)

| Claim | Repo |
|-------|------|
| Kafka microservices | **Modular monolith** + Celery + HTTP WesenseU |
| `companies` | `customers` |
| `users`/`roles` | `employees` + string `role` |

---

## Code map (P0–P2)

| Area | Path |
|------|------|
| P0 models | `guest_stay.py`, `catalog.py`, `onboarding.py`, `contact.py` |
| P2 models | `p2_extensions.py` |
| Services | `guest_stay.py`, `benchmark_requirements.py`, `ticket_task.py`, `notify_managers.py`, `inventory_task.py`, `category_availability.py`, `room_bulk.py`, `employee_availability.py` |
| APIs | `guest_stays`, `catalog`, `onboarding`, `contacts`, `fb`, extended `rooms`, `attendance`, `employees`, `departments`, `inventory`, `properties`, `room_categories`, `reports` |
| Verification | `backend/scripts/verify_requirements_flow.py` |

---

## Out of scope (not required for “complete” product flows)

- Kafka / 12 microservices deployables
- React Native mobile app
- Kubernetes manifests
- Hospital-specific templates
- PWA installable config

---

## Maintenance

Update this file when changing requirement status. Run `python scripts/verify_requirements_flow.py` after API changes.
