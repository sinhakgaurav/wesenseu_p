from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import date


class OccupancyDataPoint(BaseModel):
    date: str
    occupied: int
    vacant: int
    cleaning: int
    maintenance: int
    occupancy_rate: float


class TaskPerformancePoint(BaseModel):
    date: str
    completed: int
    pending: int
    overdue: int
    avg_completion_minutes: Optional[float] = None


class TicketTrendPoint(BaseModel):
    date: str
    opened: int
    resolved: int
    sla_breached: int


class DepartmentPerformance(BaseModel):
    department: str
    tasks_completed: int
    avg_completion_time: float
    tickets_resolved: int
    employee_count: int


class InventoryConsumption(BaseModel):
    item_name: str
    category: str
    consumed: int
    unit: str
    cost: float


class RevenuePoint(BaseModel):
    date: str
    orders_revenue: float
    order_count: int


class OccupancyReport(BaseModel):
    period: str
    data: List[OccupancyDataPoint]
    avg_occupancy_rate: float
    peak_occupancy_date: Optional[str] = None


class TaskReport(BaseModel):
    period: str
    data: List[TaskPerformancePoint]
    total_completed: int
    total_overdue: int
    avg_completion_minutes: float


class TicketReport(BaseModel):
    period: str
    data: List[TicketTrendPoint]
    total_opened: int
    total_resolved: int
    sla_breach_rate: float


class FullReport(BaseModel):
    property_id: str
    period_start: str
    period_end: str
    occupancy: OccupancyReport
    tasks: TaskReport
    tickets: TicketReport
    department_performance: List[DepartmentPerformance]
    inventory_consumption: List[InventoryConsumption]
    revenue: List[RevenuePoint]
