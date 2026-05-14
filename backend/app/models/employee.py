import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # super_admin, property_manager, dept_manager, employee, guest
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(500), nullable=False)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True)
    shift_type: Mapped[str] = mapped_column(String(20), nullable=True)  # morning, afternoon, night, rotational
    joining_date: Mapped[date] = mapped_column(Date, nullable=True)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive, suspended
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    device_token: Mapped[str] = mapped_column(String(500), nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property", back_populates="employees")
    department: Mapped["Department"] = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    assigned_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assigned_employee", foreign_keys="Task.assigned_to")
    created_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="creator", foreign_keys="Task.created_by")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
    attendance: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    check_in: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    check_out: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="present")  # present, absent, half_day, leave
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendance")
