"""contribution categories + per-cycle category kind/value

Adds global per-user contribution categories and reworks per-cycle categories
from a fixed dollar `amount` to a (`kind`, `value`) pair. Existing category
rows are migrated to kind='fixed' with value = the old amount.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Global, per-user contribution category templates.
    op.create_table(
        "contribution_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_contrib_name"),
    )
    op.create_index("ix_contribution_categories_user_id", "contribution_categories", ["user_id"])

    # Rework categories: fixed amount -> (kind, value). Backfill existing rows.
    op.add_column(
        "categories",
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="fixed"),
    )
    op.add_column(
        "categories",
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=True),
    )
    op.execute("UPDATE categories SET value = amount WHERE value IS NULL")
    op.alter_column("categories", "value", nullable=False)
    # Drop the server_default now that all rows are backfilled.
    op.alter_column("categories", "kind", server_default=None)
    op.drop_column("categories", "amount")


def downgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    # Best-effort restore: fixed categories keep their dollar value; percent
    # categories can't be recovered exactly, so fall back to 0.
    op.execute("UPDATE categories SET amount = value WHERE kind = 'fixed'")
    op.execute("UPDATE categories SET amount = 0 WHERE amount IS NULL")
    op.alter_column("categories", "amount", nullable=False)
    op.drop_column("categories", "value")
    op.drop_column("categories", "kind")

    op.drop_index("ix_contribution_categories_user_id", table_name="contribution_categories")
    op.drop_table("contribution_categories")
