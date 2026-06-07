"""P0: guest stays, catalogs, contacts, onboarding wizard

Revision ID: d4e5f6a7b8c9
Revises: c7f91a2b3d44
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c7f91a2b3d44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _col_names(insp, table: str) -> set[str]:
    if not insp.has_table(table):
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not _has_table(insp, "catalog_items"):
        op.create_table(
            "catalog_items",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("kind", sa.String(40), nullable=False),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("display_name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_system", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("kind", "code", name="uq_catalog_items_kind_code"),
        )
        op.create_index("ix_catalog_items_kind", "catalog_items", ["kind"])

    if not _has_table(insp, "guest_stays"):
        op.create_table(
            "guest_stays",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("property_id", UUID(as_uuid=True), nullable=False),
            sa.Column("room_id", UUID(as_uuid=True), nullable=False),
            sa.Column("guest_name", sa.String(200), nullable=False),
            sa.Column("guest_phone", sa.String(20), nullable=True),
            sa.Column("status", sa.String(20), server_default="active", nullable=False),
            sa.Column("check_in_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("check_out_at", sa.DateTime(), nullable=True),
            sa.Column("expected_check_out", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )
        op.create_foreign_key("fk_guest_stays_property_id", "guest_stays", "properties", ["property_id"], ["id"], ondelete="CASCADE")
        op.create_foreign_key("fk_guest_stays_room_id", "guest_stays", "rooms", ["room_id"], ["id"], ondelete="CASCADE")
        op.create_index("ix_guest_stays_room_status", "guest_stays", ["room_id", "status"])

    if not _has_table(insp, "customer_contacts"):
        op.create_table(
            "customer_contacts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("customer_id", UUID(as_uuid=True), nullable=False),
            sa.Column("contact_type", sa.String(20), nullable=False),
            sa.Column("value", sa.String(200), nullable=False),
            sa.Column("label", sa.String(80), nullable=True),
            sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )
        op.create_foreign_key("fk_customer_contacts_customer", "customer_contacts", "customers", ["customer_id"], ["id"], ondelete="CASCADE")

    if not _has_table(insp, "property_contacts"):
        op.create_table(
            "property_contacts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), nullable=False),
            sa.Column("contact_type", sa.String(20), nullable=False),
            sa.Column("value", sa.String(200), nullable=False),
            sa.Column("label", sa.String(80), nullable=True),
            sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )
        op.create_foreign_key("fk_property_contacts_property", "property_contacts", "properties", ["property_id"], ["id"], ondelete="CASCADE")

    if not _has_table(insp, "onboarding_sessions"):
        op.create_table(
            "onboarding_sessions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
            sa.Column("property_id", UUID(as_uuid=True), nullable=True),
            sa.Column("current_step", sa.String(40), server_default="business", nullable=False),
            sa.Column("step_index", sa.Integer(), server_default="0", nullable=False),
            sa.Column("payload", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("status", sa.String(20), server_default="in_progress", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )
        op.create_foreign_key("fk_onboarding_customer", "onboarding_sessions", "customers", ["customer_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key("fk_onboarding_property", "onboarding_sessions", "properties", ["property_id"], ["id"], ondelete="SET NULL")

    if not _has_table(insp, "property_catalog_selections"):
        op.create_table(
            "property_catalog_selections",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", UUID(as_uuid=True), nullable=False),
            sa.Column("catalog_item_id", UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("property_id", "catalog_item_id", name="uq_property_catalog_selection"),
        )
        op.create_foreign_key("fk_pcs_property", "property_catalog_selections", "properties", ["property_id"], ["id"], ondelete="CASCADE")
        op.create_foreign_key("fk_pcs_catalog", "property_catalog_selections", "catalog_items", ["catalog_item_id"], ["id"], ondelete="CASCADE")

    if not _has_table(insp, "room_category_amenities"):
        op.create_table(
            "room_category_amenities",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_room_category_id", UUID(as_uuid=True), nullable=False),
            sa.Column("catalog_item_id", UUID(as_uuid=True), nullable=False),
            sa.UniqueConstraint("property_room_category_id", "catalog_item_id", name="uq_room_category_amenity"),
        )
        op.create_foreign_key("fk_rca_category", "room_category_amenities", "property_room_categories", ["property_room_category_id"], ["id"], ondelete="CASCADE")
        op.create_foreign_key("fk_rca_catalog", "room_category_amenities", "catalog_items", ["catalog_item_id"], ["id"], ondelete="CASCADE")

    insp = inspect(bind)
    prc_cols = _col_names(insp, "property_room_categories")
    if "base_price" not in prc_cols and _has_table(insp, "property_room_categories"):
        op.add_column("property_room_categories", sa.Column("base_price", sa.Numeric(12, 2), nullable=True))

    room_cols = _col_names(insp, "rooms")
    if "room_view_catalog_id" not in room_cols and _has_table(insp, "rooms"):
        op.add_column("rooms", sa.Column("room_view_catalog_id", UUID(as_uuid=True), nullable=True))
        if _has_table(insp, "catalog_items"):
            op.create_foreign_key(
                "fk_rooms_room_view_catalog",
                "rooms",
                "catalog_items",
                ["room_view_catalog_id"],
                ["id"],
                ondelete="SET NULL",
            )

    order_cols = _col_names(insp, "orders")
    if "guest_stay_id" not in order_cols and _has_table(insp, "orders"):
        op.add_column("orders", sa.Column("guest_stay_id", UUID(as_uuid=True), nullable=True))
        if _has_table(insp, "guest_stays"):
            op.create_foreign_key("fk_orders_guest_stay", "orders", "guest_stays", ["guest_stay_id"], ["id"], ondelete="SET NULL")

    ticket_cols = _col_names(insp, "tickets")
    if "guest_stay_id" not in ticket_cols and _has_table(insp, "tickets"):
        op.add_column("tickets", sa.Column("guest_stay_id", UUID(as_uuid=True), nullable=True))
        if _has_table(insp, "guest_stays"):
            op.create_foreign_key("fk_tickets_guest_stay", "tickets", "guest_stays", ["guest_stay_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if _col_names(insp, "tickets") and "guest_stay_id" in _col_names(insp, "tickets"):
        op.drop_constraint("fk_tickets_guest_stay", "tickets", type_="foreignkey")
        op.drop_column("tickets", "guest_stay_id")
    if _col_names(insp, "orders") and "guest_stay_id" in _col_names(insp, "orders"):
        op.drop_constraint("fk_orders_guest_stay", "orders", type_="foreignkey")
        op.drop_column("orders", "guest_stay_id")
    if _col_names(insp, "rooms") and "room_view_catalog_id" in _col_names(insp, "rooms"):
        op.drop_constraint("fk_rooms_room_view_catalog", "rooms", type_="foreignkey")
        op.drop_column("rooms", "room_view_catalog_id")
    if _col_names(insp, "property_room_categories") and "base_price" in _col_names(insp, "property_room_categories"):
        op.drop_column("property_room_categories", "base_price")
    for t in (
        "room_category_amenities",
        "property_catalog_selections",
        "onboarding_sessions",
        "property_contacts",
        "customer_contacts",
        "guest_stays",
        "catalog_items",
    ):
        if _has_table(insp, t):
            op.drop_table(t)
