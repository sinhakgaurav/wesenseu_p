"""property_groups and configurable room categories

Revision ID: c7f91a2b3d44
Revises: 8bdb081ade0e
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "c7f91a2b3d44"
down_revision: Union[str, None] = "8bdb081ade0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property_groups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_group_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_foreign_key(
        "fk_property_groups_customer_id",
        "property_groups",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_property_groups_parent_group_id",
        "property_groups",
        "property_groups",
        ["parent_group_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "property_room_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("property_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("property_id", "code", name="uq_property_room_category_property_code"),
    )
    op.create_foreign_key(
        "fk_property_room_categories_property_id",
        "property_room_categories",
        "properties",
        ["property_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_property_room_categories_property_id",
        "property_room_categories",
        ["property_id"],
    )

    op.add_column("properties", sa.Column("property_group_id", UUID(as_uuid=True), nullable=True))
    op.add_column("properties", sa.Column("parent_property_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_properties_property_group_id",
        "properties",
        "property_groups",
        ["property_group_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_properties_parent_property_id",
        "properties",
        "properties",
        ["parent_property_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("rooms", sa.Column("property_room_category_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_rooms_property_room_category_id",
        "rooms",
        "property_room_categories",
        ["property_room_category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "room_category_benchmarks",
        sa.Column("property_room_category_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_benchmarks_property_room_category_id",
        "room_category_benchmarks",
        "property_room_categories",
        ["property_room_category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_benchmarks_property_room_category_id", "room_category_benchmarks", type_="foreignkey")
    op.drop_column("room_category_benchmarks", "property_room_category_id")

    op.drop_constraint("fk_rooms_property_room_category_id", "rooms", type_="foreignkey")
    op.drop_column("rooms", "property_room_category_id")

    op.drop_constraint("fk_properties_parent_property_id", "properties", type_="foreignkey")
    op.drop_constraint("fk_properties_property_group_id", "properties", type_="foreignkey")
    op.drop_column("properties", "parent_property_id")
    op.drop_column("properties", "property_group_id")

    op.drop_table("property_room_categories")

    op.drop_constraint("fk_property_groups_parent_group_id", "property_groups", type_="foreignkey")
    op.drop_constraint("fk_property_groups_customer_id", "property_groups", type_="foreignkey")
    op.drop_table("property_groups")
