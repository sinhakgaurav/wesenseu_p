from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class DashboardStats(BaseModel):
    total_rooms: int
    occupied_rooms: int
    vacant_rooms: int
    cleaning_pending: int
    ready_rooms: int
    maintenance_rooms: int

    active_tasks: int
    pending_tasks: int
    completed_tasks_today: int
    overdue_tasks: int

    open_tickets: int
    resolved_tickets_today: int
    critical_tickets: int

    total_employees: int
    available_employees: int
    employees_on_duty: int

    inventory_alerts: int
    surveillance_alerts: int

    recent_activities: List[Dict[str, Any]] = []
    room_status_chart: List[Dict[str, Any]] = []
    task_completion_rate: float = 0.0
    avg_ticket_resolution_time: Optional[float] = None


class PropertyDashboardSummary(BaseModel):
    property_id: str
    property_name: str
    city: Optional[str] = None
    total_rooms: int = 0
    open_tasks: int = 0
    open_tickets: int = 0
    occupancy_pct: float = 0.0


class PlatformDashboardStats(BaseModel):
    total_properties: int
    active_properties: int
    total_customers: int
    total_rooms: int
    open_tasks: int
    open_tickets: int
    total_employees: int
    properties: List[PropertyDashboardSummary] = []
