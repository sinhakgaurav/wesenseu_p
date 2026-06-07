from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    customers,
    departments,
    properties,
    property_groups,
    employees,
    rooms,
    room_categories,
    tasks,
    tickets,
    inventory,
    dashboard,
    notifications,
    feedback,
    orders,
    attendance,
    reports,
    verification,
    surveillance,
    benchmarks,
    plans,
    pages,
    super_admin,
    support,
    laundry,
    task_sla_policies,
    catalog,
    guest_stays,
    onboarding,
    contacts,
    fb,
    vendors,
    system,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(property_groups.router, prefix="/property-groups", tags=["Property Groups"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(room_categories.router, prefix="/room-categories", tags=["Room Categories"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(verification.router, prefix="/verification", tags=["AI Verification"])
api_router.include_router(surveillance.router, prefix="/surveillance", tags=["Surveillance & CCTV"])
api_router.include_router(benchmarks.router, prefix="/benchmarks", tags=["Benchmarks"])
api_router.include_router(plans.router, prefix="/plans", tags=["Plans & Pricing"])
api_router.include_router(pages.router, prefix="/pages", tags=["CMS Pages"])
api_router.include_router(super_admin.router, prefix="/admin", tags=["Super Admin Panel"])
api_router.include_router(support.router, prefix="/support", tags=["Customer Support"])
api_router.include_router(laundry.router, prefix="/laundry", tags=["Laundry"])
api_router.include_router(task_sla_policies.router, prefix="/task-sla-policies", tags=["Task SLA"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
api_router.include_router(guest_stays.router, prefix="/guest-stays", tags=["Guest Stays"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(fb.router, prefix="/fb", tags=["F&B"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
