"""P2: schedules, F&B, dept duties, room variants, task inventory rules, inventory photos

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(insp, name):
    return insp.has_table(name)


def _col_names(insp, table):
    if not insp.has_table(table):
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    cols = _col_names(insp, "inventory_items")
    if "photo_url" not in cols and insp.has_table("inventory_items"):
        op.add_column("inventory_items", sa.Column("photo_url", sa.Text(), nullable=True))

    if not _has_table(insp, "department_catalog_duties"):
        op.create_table(
            "department_catalog_duties",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("catalog_item_id", UUID(as_uuid=True), sa.ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False),
            sa.UniqueConstraint("department_id", "catalog_item_id", name="uq_dept_catalog_duty"),
        )

    if not _has_table(insp, "property_schedules"):
        op.create_table(
            "property_schedules",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("day_of_week", sa.Integer(), nullable=False),
            sa.Column("open_time", sa.Time(), nullable=False),
            sa.Column("close_time", sa.Time(), nullable=False),
            sa.Column("is_closed", sa.Boolean(), server_default="false"),
        )

    if not _has_table(insp, "employee_schedules"):
        op.create_table(
            "employee_schedules",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("weekly_off_days", JSONB(), server_default="[]"),
            sa.Column("lunch_start", sa.Time(), nullable=True),
            sa.Column("lunch_end", sa.Time(), nullable=True),
        )

    if not _has_table(insp, "property_outlets"):
        op.create_table(
            "property_outlets",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("outlet_type", sa.String(50), server_default="restaurant"),
            sa.Column("is_active", sa.Boolean(), server_default="true"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        )

    if not _has_table(insp, "property_menu_items"):
        op.create_table(
            "property_menu_items",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("outlet_id", UUID(as_uuid=True), sa.ForeignKey("property_outlets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("catalog_item_id", UUID(as_uuid=True), sa.ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("photo_url", sa.Text(), nullable=True),
            sa.Column("is_available", sa.Boolean(), server_default="true"),
        )

    if not _has_table(insp, "room_variants"):
        op.create_table(
            "room_variants",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
            sa.Column("property_room_category_id", UUID(as_uuid=True), sa.ForeignKey("property_room_categories.id", ondelete="CASCADE"), nullable=False),
            sa.Column("room_view_catalog_id", UUID(as_uuid=True), sa.ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True),
            sa.Column("variant_label", sa.String(120), nullable=False),
            sa.Column("room_count", sa.Integer(), server_default="1"),
            sa.Column("price_override", sa.Numeric(10, 2), nullable=True),
            sa.Column("floor_number", sa.Integer(), nullable=True),
            sa.Column("room_number_prefix", sa.String(20), nullable=True),
            sa.Column("start_number", sa.Integer(), server_default="101"),
        )

    if not _has_table(insp, "task_inventory_rules"):
        op.create_table(
            "task_inventory_rules",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("inventory_item_id", UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
            sa.Column("quantity_per_task", sa.Integer(), server_default="1"),
            sa.Column("is_active", sa.Boolean(), server_default="true"),
            sa.UniqueConstraint("property_id", "task_type", "inventory_item_id", name="uq_task_inv_rule"),
        )


def downgrade():
    for t in (
        "task_inventory_rules",
        "room_variants",
        "property_menu_items",
        "property_outlets",
        "employee_schedules",
        "property_schedules",
        "department_catalog_duties",
    ):
        op.drop_table(t)
    bind = op.get_bind()
    insp = inspect(bind)
    if "photo_url" in _col_names(insp, "inventory_items"):
        op.drop_column("inventory_items", "photo_url")
