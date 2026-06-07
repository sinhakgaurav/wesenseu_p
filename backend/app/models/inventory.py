import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="vendor")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # Toiletries, Cleaning, Towels, Bedsheets, Kitchen, Medical, Guest Consumables, Laundry
    unit: Mapped[str] = mapped_column(String(20), default="piece")  # piece, kg, liter, box
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=5)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property", back_populates="inventory_items")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="inventory_items")
    transactions: Mapped[list["InventoryTransaction"]] = relationship("InventoryTransaction", back_populates="inventory_item")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # IN, OUT
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str] = mapped_column(String(20), nullable=True)  # ticket, task, manual
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    performed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    inventory_item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="transactions")
