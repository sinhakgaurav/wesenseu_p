# CRUD & Admin UI verification matrix

**Last updated:** 2026-05-20  
**Scope:** Core Monitour entities — REST API CRUD + admin React UI at `/admin/*`.

## Legend

| API | REST create/read/update/delete (or soft-delete) |
| UI | Page or section in the admin panel |

| Status | Meaning |
|--------|---------|
| ✅ | Implemented |
| — | Not required for this entity |

---

## Summary

| Area | API | Admin UI |
|------|-----|----------|
| Properties | ✅ | ✅ `/admin/properties` (super_admin) |
| Property settings | ✅ schedules + contacts | ✅ `/admin/property-settings` |
| Departments | ✅ + duties | ✅ manager + duties picker |
| Employees | ✅ + CSV import | ✅ import + deactivate |
| Rooms | ✅ + bulk | ✅ Rooms page |
| Room categories | ✅ + amenities | ✅ amenities + availability |
| Catalog | ✅ | ✅ via onboarding + category amenities |
| Guest stays | ✅ | ✅ `/admin/guests` |
| Tasks | ✅ + media + benchmark | ✅ upload + WesenseU submit |
| Task SLA | ✅ | ✅ `/admin/task-sla` |
| Tickets | ✅ | ✅ `/admin/tickets` |
| Inventory | ✅ + photo + task rules | ✅ edit/delete/photo |
| Vendors | ✅ | ✅ `/admin/vendors` |
| F&B | ✅ | ✅ `/admin/fnb` |
| Contacts | ✅ | ✅ property settings + onboarding |
| Onboarding | ✅ + list sessions | ✅ `/admin/onboarding` |
| Attendance | ✅ + import/schedule | ✅ summary + reports |
| Benchmarks | ✅ | ✅ `/admin/benchmarks` |
| Notifications | ✅ | ✅ Header bell (REST poll) |

**Out of scope (documented):** Kafka, React Native app, forgot-password email flow, WebSocket push (WS endpoint exists; UI uses REST).

---

## Entity matrix

### Properties & setup

| Entity | API prefix | C | R | U | D | Admin UI |
|--------|------------|---|---|---|---|----------|
| Property | `/properties` | ✅ | ✅ | ✅ | ✅ soft | Properties (super_admin) |
| Property schedule | `/properties/{id}/schedules` | ✅ PUT | ✅ GET | ✅ PUT | ✅ replace | Property settings |
| Property contact | `/contacts/properties/{id}` | ✅ | ✅ | ✅ PATCH | ✅ | Property settings |
| Customer contact | `/contacts/customers/{id}` | ✅ | ✅ | ✅ PATCH | ✅ | Onboarding wizard |
| Onboarding session | `/onboarding/sessions` | ✅ | ✅ list+get | ✅ PATCH | — | Onboarding wizard |
| Catalog item | `/catalog/items` | ✅ | ✅ | ✅ PATCH | ✅ soft | Onboarding / amenities |
| Property features | `/catalog/properties/{id}/features` | — | ✅ | ✅ PUT | — | Onboarding |
| Room category amenity | `/catalog/room-categories/{id}/amenities` | — | ✅ GET | ✅ PUT | — | Room categories |

### Operations

| Entity | API prefix | C | R | U | D | Admin UI |
|--------|------------|---|---|---|---|----------|
| Department | `/departments` | ✅ | ✅ | ✅ | ✅ soft | Departments |
| Dept duties | `/departments/{id}/duties` | — | ✅ | ✅ PUT | — | Departments duties modal |
| Employee | `/employees` | ✅ | ✅ | ✅ | ✅ inactive | Employees + CSV |
| Room | `/rooms` | ✅ | ✅ | ✅ | ✅ | Rooms + bulk in onboarding |
| Room bulk | `/rooms/bulk` | ✅ | — | — | — | Onboarding + Rooms |
| Guest stay | `/guest-stays` | ✅ | ✅ | ✅ checkout | — | Guests |
| Task | `/tasks` | ✅ | ✅ | ✅ status | ✅ soft + restore | Tasks |
| Task media | `/tasks/{id}/upload-media` | ✅ | — | — | — | Tasks detail |
| Task SLA policy | `/task-sla-policies` | ✅ | ✅ | ✅ | ✅ soft | Task SLA page |
| Ticket | `/tickets` | ✅ | ✅ | ✅ | ✅ soft + restore | Tickets |
| Inventory item | `/inventory/items` | ✅ | ✅ | ✅ | ✅ soft | Inventory |
| Inventory photo | `/inventory/items/{id}/photo` | ✅ | — | — | — | Inventory |
| Task inventory rule | `/inventory/task-rules` | ✅ | ✅ | — | — | Seeded / API |
| Vendor | `/vendors` | ✅ | ✅ | ✅ | ✅ soft | Vendors page |

### F&B

| Entity | API | C | R | U | D | Admin UI |
|--------|-----|---|---|---|---|----------|
| Outlet | `/fb/properties/{id}/outlets` | ✅ | ✅ | ✅ PATCH | ✅ soft | F&B page |
| Menu item | `/fb/outlets/{id}/menu` | ✅ | ✅ | ✅ PATCH | ✅ soft | F&B page |

### Attendance & reporting

| Entity | API | Admin UI |
|--------|-----|----------|
| Attendance summary/history | `/attendance/*` | Attendance page |
| Manager records/import | `/attendance/records`, `/import` | Reports + API |
| Reports attendance | `/reports/attendance` | Reports page |

### Soft delete & database introspection

| Feature | Endpoint | Notes |
|---------|----------|-------|
| Soft delete helper | `app/db/soft_delete.py` | Sets `is_active=false` and `deleted_at` when columns exist |
| Tables with `is_active` + `deleted_at` | contacts, tasks, tickets, feedback, pages, orders | Migration `f6a7b8c9d0e1` |
| List with trash | `?include_deleted=true` | tasks, tickets, feedback, orders, contacts, pages (admin) |
| Restore | `POST …/{id}/restore` | tasks, tickets, feedback, contacts, pages |
| DB table browser | `GET /system/db-tables` | super_admin only; row counts + column list |
| Admin UI | Super Admin → **database** tab | Calls `/system/db-tables` |

Many other entities use **`is_active=false`** only (properties, vendors, catalog, inventory, etc.) without `deleted_at`.

---

## Seeders & sample data

| Script | Purpose |
|--------|---------|
| `app/db/init_db.py` | Plans, demo property, users, rooms, inventory |
| `app/db/seed_catalog.py` | Amenities, duties, dishes, features |
| `app/db/seed_comprehensive.py` | Tickets, tasks, guest stays, orders |
| `app/db/seed_task_inventory_rules.py` | Cleaning → inventory deduction rules |
| `app/db/seed_p2_sample.py` | Vendors, F&B menu, contacts, schedules, dept duty link, onboarding session |

Run after migrations:

```bash
docker compose exec backend python -m app.db.init_db
```

---

## Verification commands

```bash
# Route smoke (no auth; expects 401/404/422, not 405)
docker compose exec backend python scripts/verify_requirements_flow.py

# Login smoke
# manager@grandpalace.com / Manager@123 → http://localhost:3000/admin
```

---

## Checklist alignment

- **Flow requirements:** see `docs/REQUIREMENTS_FLOW_VERIFICATION.md` — flows marked **Done** where API + primary UI exist.
- **Architecture spec:** see `docs/ARCHITECTURE_SPEC_CHECKLIST.md` — CRUD/UI rows updated 2026-05-20.
