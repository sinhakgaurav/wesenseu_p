# Events and integrations (Monitour backend)

This document answers whether Monitour is “event-driven” and lists the main **event-like** mechanisms in the codebase.

## Is the system event-driven?

**Partially, in a practical sense — not as a formal event-sourced or enterprise message-bus architecture.**

- **Celery** is used for **asynchronous tasks** (scheduled and on-demand work off the HTTP request path).
- **HTTP callbacks** from WesenseU complete long-running AI flows.
- **WebSockets** deliver **real-time** updates to connected clients.
- **Domain records** such as `SurveillanceEvent` store **things that happened** for reporting and UI, but they are ordinary database rows, not a separate event store or pub/sub backbone.

There is **no** central broker (e.g. Kafka/RabbitMQ) described in this repo for arbitrary domain events; integration is mainly **REST + WebSockets + Celery + email**.

## Kinds of “events” in use

### 1. Celery tasks (background jobs)

| Task name | Purpose |
|-----------|---------|
| `app.worker.tasks.check_sla_breaches` | Find tickets past SLA, flag breaches, email property managers. |
| `app.worker.tasks.check_low_stock` | Scan inventory below minimum, email alerts. |
| `app.worker.tasks.escalate_overdue_tasks` | Bump escalation on overdue tasks, email assignees. |
| `app.worker.tasks.send_task_assigned_email` | Send email when a task is assigned. |
| `app.worker.tasks.dispatch_to_wesenseu` | Download verification images, POST multipart to WesenseU, update `RoomVerification` queue state. |

These are **queued work units**, not domain events published to subscribers.

### 2. HTTP callbacks (external system → Monitour)

- **WesenseU verification callback** — WesenseU POSTs results to Monitour (see verification routes); this is a classic **webhook** pattern after async processing.

### 3. WebSocket “events” (server → browser)

- **`/api/v1/notifications/ws/{user_id}`** — persistent connections; server can push JSON payloads (e.g. `pong` for health checks). Used with in-app notifications that list channels such as `websocket` and `push` in the `Notification` model.

### 4. Notification channels (metadata, not a bus)

- Stored on notifications as JSON (e.g. `push`, `email`, `sms`, `websocket`). This describes **intended delivery**, not a separate event pipeline.

### 5. Stored surveillance “events”

- **`SurveillanceEvent`** rows represent detections (motion, hygiene, obstruction, etc.) with severity and timestamps — **audit/reporting entities**, not streaming events unless you add your own consumers.

### 6. Room / ticket lifecycle (implicit “events”)

- Status changes on rooms, tickets, tasks, orders are **state transitions** in the database (sometimes with audit rows such as `RoomAuditLog`). These are not emitted to a global event bus by default.

---

If you later need true event-driven boundaries (e.g. `RoomCheckedOut` → fan-out to analytics, billing, and IoT), you would typically add a **message broker** or **outbox pattern** on top of the current Celery and HTTP callback model.
