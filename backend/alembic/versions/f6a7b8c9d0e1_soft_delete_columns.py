"""Add is_active + deleted_at for soft delete on core transactional tables.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "customer_contacts",
    "property_contacts",
    "tasks",
    "tickets",
    "feedback",
    "pages",
    "orders",
)


def _col_names(insp, table: str) -> set[str]:
    if not insp.has_table(table):
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    for table in TABLES:
        if not insp.has_table(table):
            continue
        cols = _col_names(insp, table)
        if "is_active" not in cols:
            op.add_column(
                table,
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            )
        if "deleted_at" not in cols:
            op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    for table in TABLES:
        if not insp.has_table(table):
            continue
        cols = _col_names(insp, table)
        if "deleted_at" in cols:
            op.drop_column(table, "deleted_at")
        if "is_active" in cols:
            op.drop_column(table, "is_active")
