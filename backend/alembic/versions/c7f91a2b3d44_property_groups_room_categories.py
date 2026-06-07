"""property_groups and configurable room categories

Revision ID: c7f91a2b3d44
Revises: 8bdb081ade0e
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision: str = "c7f91a2b3d44"
down_revision: Union[str, None] = "8bdb081ade0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_names(insp, table: str) -> set[str]:
    return {fk["name"] for fk in insp.get_foreign_keys(table) if fk.get("name")}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("property_groups"):
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

    if not insp.has_table("property_room_categories"):
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

    if insp.has_table("properties"):
        def _prop_cols():
            return {c["name"] for c in inspect(bind).get_columns("properties")}

        def _prop_fks():
            return _fk_names(inspect(bind), "properties")

        if "property_group_id" not in _prop_cols():
            op.add_column("properties", sa.Column("property_group_id", UUID(as_uuid=True), nullable=True))
        if "fk_properties_property_group_id" not in _prop_fks() and inspect(bind).has_table("property_groups"):
            op.create_foreign_key(
                "fk_properties_property_group_id",
                "properties",
                "property_groups",
                ["property_group_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if "parent_property_id" not in _prop_cols():
            op.add_column("properties", sa.Column("parent_property_id", UUID(as_uuid=True), nullable=True))
        if "fk_properties_parent_property_id" not in _prop_fks():
            op.create_foreign_key(
                "fk_properties_parent_property_id",
                "properties",
                "properties",
                ["parent_property_id"],
                ["id"],
                ondelete="SET NULL",
            )

    if insp.has_table("rooms"):
        def _room_cols():
            return {c["name"] for c in inspect(bind).get_columns("rooms")}

        def _room_fks():
            return _fk_names(inspect(bind), "rooms")

        if "property_room_category_id" not in _room_cols():
            op.add_column("rooms", sa.Column("property_room_category_id", UUID(as_uuid=True), nullable=True))
        if "fk_rooms_property_room_category_id" not in _room_fks() and inspect(bind).has_table(
            "property_room_categories"
        ):
            op.create_foreign_key(
                "fk_rooms_property_room_category_id",
                "rooms",
                "property_room_categories",
                ["property_room_category_id"],
                ["id"],
                ondelete="SET NULL",
            )

    if insp.has_table("room_category_benchmarks"):
        def _bench_cols():
            return {c["name"] for c in inspect(bind).get_columns("room_category_benchmarks")}

        def _bench_fks():
            return _fk_names(inspect(bind), "room_category_benchmarks")

        if "property_room_category_id" not in _bench_cols():
            op.add_column(
                "room_category_benchmarks",
                sa.Column("property_room_category_id", UUID(as_uuid=True), nullable=True),
            )
        if "fk_benchmarks_property_room_category_id" not in _bench_fks() and inspect(bind).has_table(
            "property_room_categories"
        ):
            op.create_foreign_key(
                "fk_benchmarks_property_room_category_id",
                "room_category_benchmarks",
                "property_room_categories",
                ["property_room_category_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("room_category_benchmarks"):
        if "fk_benchmarks_property_room_category_id" in _fk_names(insp, "room_category_benchmarks"):
            op.drop_constraint("fk_benchmarks_property_room_category_id", "room_category_benchmarks", type_="foreignkey")
        if "property_room_category_id" in {c["name"] for c in insp.get_columns("room_category_benchmarks")}:
            op.drop_column("room_category_benchmarks", "property_room_category_id")

    if insp.has_table("rooms"):
        if "fk_rooms_property_room_category_id" in _fk_names(insp, "rooms"):
            op.drop_constraint("fk_rooms_property_room_category_id", "rooms", type_="foreignkey")
        if "property_room_category_id" in {c["name"] for c in insp.get_columns("rooms")}:
            op.drop_column("rooms", "property_room_category_id")

    if insp.has_table("properties"):
        if "fk_properties_parent_property_id" in _fk_names(insp, "properties"):
            op.drop_constraint("fk_properties_parent_property_id", "properties", type_="foreignkey")
        if "fk_properties_property_group_id" in _fk_names(insp, "properties"):
            op.drop_constraint("fk_properties_property_group_id", "properties", type_="foreignkey")
        cols = {c["name"] for c in insp.get_columns("properties")}
        if "parent_property_id" in cols:
            op.drop_column("properties", "parent_property_id")
        if "property_group_id" in cols:
            op.drop_column("properties", "property_group_id")

    if insp.has_table("property_room_categories"):
        op.drop_table("property_room_categories")

    if insp.has_table("property_groups"):
        op.drop_constraint("fk_property_groups_parent_group_id", "property_groups", type_="foreignkey")
        op.drop_constraint("fk_property_groups_customer_id", "property_groups", type_="foreignkey")
        op.drop_table("property_groups")
