# Monitour feature availability matrix

**Last updated:** 2026-05-24

Legend: **Yes** = implemented (API + primary UI where applicable) · **Partial** = backend or limited UI · **Planned** = marketing/spec only, not built

| Feature | Status | Notes |
|---------|--------|-------|
| Room management | **Yes** | `/admin/rooms`, bulk, categories, QR |
| Task & ticket system | **Yes** | `/admin/tasks`, `/admin/tickets`, SLA on tickets |
| Guest portal (QR) | **Yes** | `/guest/:roomId`, feedback & tickets via QR |
| Inventory management | **Yes** | `/admin/inventory`, photos, task rules |
| Orders / room service | **Yes** | `/admin/orders` |
| Attendance tracking | **Yes** | `/admin/attendance`, import |
| AI room verification | **Partial** | WesenseU + Celery; needs worker + WesenseU on :8001 |
| CCTV surveillance | **Partial** | `/admin/surveillance`, cameras/alerts API; not full VMS |
| Benchmark management | **Yes** | `/admin/benchmarks`, per room category |
| Advanced analytics | **Partial** | `/admin/reports` charts; not full BI / predictive |
| Multi-property dashboard | **Partial** | Customer B2B dashboard API; super_admin stats; no unified “all properties” ops dashboard |
| AI customer support chat | **Partial** | Public widget + `/support`; not embedded in admin |
| White-label branding | **Planned** | Listed on Enterprise/Custom plans only |
| IoT / Smart Lock | **Planned** | Plan copy only |
| Dedicated infrastructure | **Planned** | Ops/deployment, not app feature |
| SLA-backed support | **Partial** | Task SLA policies + ticket SLA hours; not support-ticket SLA product |

## Super admin (Monitour platform operator)

| Capability | Status | Where |
|------------|--------|-------|
| Notifications (bell) | **Yes** | Header on all `/admin/*` pages (polls `/notifications`) |
| Business → Property navigation | **Yes** | Admin Panel → **Businesses** tab (`GET /admin/hierarchy`) |
| Property approve / decline | **Yes** | Approvals tab + per-property on Businesses tab |
| Business approve / suspend | **Yes** | `PATCH /admin/customers/{id}/status` on Businesses tab |
| Plans CRUD | **Yes** | Admin Panel → **Plans** (`/plans` API) |
| CMS / page content | **Yes** | Admin Panel → **CMS** (CKEditor HTML body, publish) |
| Module toggles per property | **Yes** | Admin Panel → **Modules** |
| Cross-property employees | **Yes** | Admin Panel → **Employees** |
| Database tables browser | **Yes** | Admin Panel → **Database** |
| Properties CRUD | **Yes** | Sidebar → **Properties** |

## Approval system scope

| Level | Approve | Decline | Implementation |
|-------|---------|---------|----------------|
| **Property** | Yes | Yes (reject) | `PropertyApproval` + `PATCH /admin/approvals/{id}` |
| **Business (customer)** | Yes (active) | Yes (suspend/cancel) | `PATCH /admin/customers/{id}/status` |
| **Individual room/task/etc.** | N/A | N/A | Operational CRUD, not approval workflow |

Property creation should create a `property_approvals` row (pending) until super_admin approves.
