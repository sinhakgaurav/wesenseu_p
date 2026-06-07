#!/usr/bin/env python3
"""Append P0–P2 flow endpoints to Monitour.postman_collection.json (idempotent)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTION_PATH = ROOT / "Monitour.postman_collection.json"

NEW_VARS = [
    {"key": "categoryId", "value": "", "type": "string"},
    {"key": "outletId", "value": "", "type": "string"},
    {"key": "vendorId", "value": "", "type": "string"},
    {"key": "sessionId", "value": "", "type": "string"},
    {"key": "guestStayId", "value": "", "type": "string"},
    {"key": "contactId", "value": "", "type": "string"},
    {"key": "catalogItemId", "value": "", "type": "string"},
    {"key": "menuItemId", "value": "", "type": "string"},
    {"key": "slaPolicyId", "value": "", "type": "string"},
]

def req(name: str, method: str, path: list[str], *, query=None, body=None, desc=None, formdata=None):
    url = {"raw": "{{apiBase}}/" + "/".join(path), "host": ["{{apiBase}}"], "path": path}
    if query:
        url["query"] = query
    r = {"name": name, "request": {"method": method, "url": url}}
    if desc:
        r["request"]["description"] = desc
    if body is not None:
        r["request"]["header"] = [{"key": "Content-Type", "value": "application/json"}]
        r["request"]["body"] = {"mode": "raw", "raw": body}
    if formdata:
        r["request"]["body"] = {"mode": "formdata", "formdata": formdata}
    return r


def folder(name: str, items: list) -> dict:
    return {"name": name, "item": items}


NEW_FOLDERS = [
    folder("📋 Catalog", [
        req("List Catalog Kinds", "GET", ["catalog", "kinds"]),
        req("List Catalog Items", "GET", ["catalog", "items"], query=[{"key": "kind", "value": "amenity"}]),
        req("Create Catalog Item", "POST", ["catalog", "items"], body='{\n  "kind": "amenity",\n  "display_name": "Mini Bar"\n}'),
        req("Update Catalog Item", "PATCH", ["catalog", "items", "{{catalogItemId}}"], body='{\n  "display_name": "Updated name"\n}'),
        req("Delete Catalog Item", "DELETE", ["catalog", "items", "{{catalogItemId}}"]),
        req("Get Property Features", "GET", ["catalog", "properties", "{{propertyId}}", "features"]),
        req("Set Property Features", "PUT", ["catalog", "properties", "{{propertyId}}", "features"], body='{\n  "catalog_item_ids": []\n}'),
        req("Get Room Category Amenities", "GET", ["catalog", "room-categories", "{{categoryId}}", "amenities"]),
        req("Set Room Category Amenities", "PUT", ["catalog", "room-categories", "{{categoryId}}", "amenities"], body='{\n  "catalog_item_ids": []\n}'),
    ]),
    folder("🚀 Onboarding", [
        req("List Onboarding Steps", "GET", ["onboarding", "steps"]),
        req("List Onboarding Sessions", "GET", ["onboarding", "sessions"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Create Onboarding Session", "POST", ["onboarding", "sessions"], body='{\n  "property_id": "{{propertyId}}"\n}'),
        req("Get Onboarding Session", "GET", ["onboarding", "sessions", "{{sessionId}}"]),
        req("Update Onboarding Session", "PATCH", ["onboarding", "sessions", "{{sessionId}}"], body='{\n  "current_step": "inventory",\n  "payload_patch": {}\n}'),
    ]),
    folder("📞 Contacts", [
        req("List Property Contacts", "GET", ["contacts", "properties", "{{propertyId}}"]),
        req("Add Property Contact", "POST", ["contacts", "properties", "{{propertyId}}"], body='{\n  "contact_type": "phone",\n  "value": "+91-8000000000",\n  "label": "Front desk"\n}'),
        req("Update Property Contact", "PATCH", ["contacts", "properties", "{{propertyId}}", "{{contactId}}"], body='{\n  "value": "+91-8111111111"\n}'),
        req("Delete Property Contact", "DELETE", ["contacts", "properties", "{{propertyId}}", "{{contactId}}"]),
        req("List Customer Contacts", "GET", ["contacts", "customers", "{{customerId}}"], desc="Set customerId from B2B customer UUID"),
        req("Add Customer Contact", "POST", ["contacts", "customers", "{{customerId}}"], body='{\n  "contact_type": "email",\n  "value": "owner@example.com"\n}'),
    ]),
    folder("🍽️ F&B", [
        req("List Outlets", "GET", ["fb", "properties", "{{propertyId}}", "outlets"]),
        req("Create Outlet", "POST", ["fb", "properties", "{{propertyId}}", "outlets"], body='{\n  "property_id": "{{propertyId}}",\n  "name": "Main Restaurant",\n  "outlet_type": "restaurant"\n}'),
        req("Update Outlet", "PATCH", ["fb", "outlets", "{{outletId}}"], body='{\n  "name": "Updated Restaurant"\n}'),
        req("Delete Outlet", "DELETE", ["fb", "outlets", "{{outletId}}"]),
        req("List Menu Items", "GET", ["fb", "outlets", "{{outletId}}", "menu"]),
        req("Add Menu Item", "POST", ["fb", "outlets", "{{outletId}}", "menu"], body='{\n  "name": "Masala Dosa",\n  "price": 180\n}'),
        req("Update Menu Item", "PATCH", ["fb", "menu", "{{menuItemId}}"], body='{\n  "price": 200\n}'),
        req("Delete Menu Item", "DELETE", ["fb", "menu", "{{menuItemId}}"]),
    ]),
    folder("🚚 Vendors", [
        req("List Vendors", "GET", ["vendors"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Create Vendor", "POST", ["vendors"], body='{\n  "property_id": "{{propertyId}}",\n  "name": "Linen Supply Co",\n  "phone": "+91-9000000001"\n}'),
        req("Update Vendor", "PATCH", ["vendors", "{{vendorId}}"], body='{\n  "phone": "+91-9000000002"\n}'),
        req("Delete Vendor", "DELETE", ["vendors", "{{vendorId}}"]),
    ]),
    folder("🧳 Guest Stays", [
        req("List Guest Stays", "GET", ["guest-stays"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Get Guest Stay", "GET", ["guest-stays", "{{guestStayId}}"]),
        req("Guest Stay Folio", "GET", ["guest-stays", "{{guestStayId}}", "folio"]),
        req("Guest Check-in (Room)", "POST", ["rooms", "{{roomId}}", "guest-check-in"], body='{\n  "guest_name": "John Doe",\n  "guest_phone": "+91-9999999999"\n}'),
        req("Room Checkout", "POST", ["rooms", "{{roomId}}", "checkout"], body="{}"),
    ]),
    folder("⏱️ Task SLA", [
        req("List SLA Policies", "GET", ["task-sla-policies"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Create SLA Policy", "POST", ["task-sla-policies"], body='{\n  "property_id": "{{propertyId}}",\n  "task_type": "cleaning",\n  "service_type": "*",\n  "sla_minutes": 120,\n  "root_cause_category": "capacity"\n}'),
        req("Update SLA Policy", "PATCH", ["task-sla-policies", "{{slaPolicyId}}"], body='{\n  "sla_minutes": 90\n}'),
        req("Delete SLA Policy", "DELETE", ["task-sla-policies", "{{slaPolicyId}}"]),
    ]),
    folder("🏷️ Room Categories", [
        req("List Room Categories", "GET", ["room-categories"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Category Availability", "GET", ["room-categories", "availability"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Create Room Category", "POST", ["room-categories"], body='{\n  "property_id": "{{propertyId}}",\n  "code": "deluxe",\n  "display_name": "Deluxe"\n}'),
        req("Update Room Category", "PATCH", ["room-categories", "{{categoryId}}"], body='{\n  "display_name": "Deluxe Updated"\n}'),
        req("Deactivate Room Category", "DELETE", ["room-categories", "{{categoryId}}"]),
    ]),
    folder("🏢 Property Schedules (P2)", [
        req("Get Property Schedules", "GET", ["properties", "{{propertyId}}", "schedules"]),
        req("Set Property Schedules", "PUT", ["properties", "{{propertyId}}", "schedules"], body='{\n  "schedules": [\n    {"day_of_week": 0, "open_time": "06:00:00", "close_time": "23:00:00", "is_closed": false}\n  ]\n}'),
    ]),
    folder("🏛️ Department Duties (P2)", [
        req("Get Department Duties", "GET", ["departments", "{{departmentId}}", "duties"]),
        req("Set Department Duties", "PUT", ["departments", "{{departmentId}}", "duties"], body='{\n  "catalog_item_ids": []\n}'),
    ]),
    folder("🛏️ Rooms Bulk (P2)", [
        req("Bulk Create Rooms", "POST", ["rooms", "bulk"], body='{\n  "property_id": "{{propertyId}}",\n  "property_room_category_id": "{{categoryId}}",\n  "start_number": 201,\n  "count": 5,\n  "room_number_prefix": ""\n}'),
        req("Create Room Variants", "POST", ["rooms", "variants"], body='{\n  "property_id": "{{propertyId}}",\n  "property_room_category_id": "{{categoryId}}",\n  "variant_label": "Pool View",\n  "room_count": 3,\n  "create_rooms": true\n}'),
    ]),
    folder("✅ Tasks (extended)", [
        req("Auto-assign Task", "POST", ["tasks", "{{taskId}}", "auto-assign"]),
        req("Benchmark Requirements", "GET", ["tasks", "{{taskId}}", "benchmark-requirements"]),
        req("Delete Task", "DELETE", ["tasks", "{{taskId}}"]),
    ]),
    folder("📦 Inventory (extended)", [
        req("Upload Item Photo", "POST", ["inventory", "items", "{{itemId}}", "photo"], formdata=[{"key": "file", "type": "file", "src": []}]),
        req("Deactivate Inventory Item", "DELETE", ["inventory", "items", "{{itemId}}"]),
        req("List Task Inventory Rules", "GET", ["inventory", "task-rules"], query=[{"key": "property_id", "value": "{{propertyId}}"}]),
        req("Create Task Inventory Rule", "POST", ["inventory", "task-rules"], body='{\n  "property_id": "{{propertyId}}",\n  "task_type": "cleaning",\n  "inventory_item_id": "{{itemId}}",\n  "quantity_per_task": 1\n}'),
    ]),
    folder("👥 Employees (extended)", [
        req("Import Employees CSV", "POST", ["employees", "import"], formdata=[{"key": "file", "type": "file", "src": []}]),
    ]),
    folder("🕐 Attendance (extended)", [
        req("Create Attendance Record", "POST", ["attendance", "records"], body='{\n  "employee_id": "{{employeeId}}",\n  "record_date": "2026-05-20",\n  "status": "leave"\n}'),
        req("Import Attendance CSV", "POST", ["attendance", "import"], formdata=[{"key": "file", "type": "file", "src": []}]),
        req("Update Employee Schedule", "PUT", ["attendance", "employees", "{{employeeId}}", "schedule"], body='{\n  "weekly_off_days": [0],\n  "lunch_start": "13:00:00",\n  "lunch_end": "14:00:00"\n}'),
    ]),
    folder("📈 Reports (extended)", [
        req("Attendance Report", "GET", ["reports", "attendance"], query=[{"key": "month", "value": "5"}, {"key": "year", "value": "2026"}]),
    ]),
]

MARKER = "📋 Catalog"  # first new folder name


def main() -> None:
    data = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    existing_names = {f["name"] for f in data["item"] if f.get("name")}
    if MARKER in existing_names:
        print("Postman collection already includes P2 folders — skipping.")
        return

    keys = {v["key"] for v in data.get("variable", [])}
    for v in NEW_VARS:
        if v["key"] not in keys:
            data["variable"].append(v)

    # Insert before Health folder
    items = data["item"]
    health_idx = next(i for i, f in enumerate(items) if f.get("name") == "🩺 Health")
    for i, folder_obj in enumerate(NEW_FOLDERS):
        items.insert(health_idx + i, folder_obj)

    desc = data["info"].get("description", "")
    if "P0–P2 flows" not in desc:
        data["info"]["description"] = (
            desc.rstrip()
            + "\n\n## P0–P2 flows (2026-05-20)\n"
            + "Folders: Catalog, Onboarding, Contacts, F&B, Vendors, Guest Stays, Task SLA, "
            + "Room Categories, Property Schedules, Department Duties, Rooms Bulk, extended Tasks/Inventory/Attendance/Reports.\n"
            + "See `docs/CRUD_VERIFICATION.md` and `docs/REQUIREMENTS_FLOW_VERIFICATION.md`."
        )

    COLLECTION_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched {COLLECTION_PATH.name}: added {len(NEW_FOLDERS)} folders.")


if __name__ == "__main__":
    main()
