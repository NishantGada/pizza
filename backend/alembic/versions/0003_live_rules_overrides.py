"""live rules + per-cycle overrides

Unifies how recurring rules attach to a cycle. Instead of snapshotting rule
values onto each cycle, a cycle now inherits the live global settings and
contribution categories, storing a row only when it overrides one.

* pay_cycles: savings_pct / retirement_401k_pct / hsa_amount become nullable
  overrides (NULL = inherit global). Existing snapshots are discarded so every
  cycle reflects the current global settings.
* categories: gains a nullable contribution_category_id FK (override target)
  and a unique (pay_cycle_id, contribution_category_id); name becomes nullable
  (ad-hoc only). Existing per-cycle copies are discarded so cycles inherit the
  live global categories.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pay_cycles: rule columns become nullable overrides; discard old snapshots.
    op.alter_column("pay_cycles", "savings_pct", existing_type=sa.Numeric(5, 4), nullable=True)
    op.alter_column(
        "pay_cycles", "retirement_401k_pct", existing_type=sa.Numeric(5, 4), nullable=True
    )
    op.alter_column("pay_cycles", "hsa_amount", existing_type=sa.Numeric(12, 2), nullable=True)
    op.execute(
        "UPDATE pay_cycles SET savings_pct = NULL, retirement_401k_pct = NULL, hsa_amount = NULL"
    )

    # categories: discard stale per-cycle copies, then reshape into overrides.
    op.execute("DELETE FROM categories")
    op.add_column(
        "categories", sa.Column("contribution_category_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_categories_contribution_category_id",
        "categories",
        "contribution_categories",
        ["contribution_category_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_cycle_override", "categories", ["pay_cycle_id", "contribution_category_id"]
    )
    op.alter_column("categories", "name", existing_type=sa.String(length=120), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM categories")
    op.alter_column(
        "categories", "name", existing_type=sa.String(length=120), nullable=False
    )
    op.drop_constraint("uq_cycle_override", "categories", type_="unique")
    op.drop_constraint(
        "fk_categories_contribution_category_id", "categories", type_="foreignkey"
    )
    op.drop_column("categories", "contribution_category_id")

    # Restore NOT NULL rule columns, backfilling from the user's global settings.
    op.execute(
        """
        UPDATE pay_cycles pc SET
            savings_pct = COALESCE(pc.savings_pct, bs.savings_pct, 0),
            retirement_401k_pct = COALESCE(pc.retirement_401k_pct, bs.retirement_401k_pct, 0),
            hsa_amount = COALESCE(pc.hsa_amount, bs.hsa_per_cycle, 0)
        FROM budget_settings bs
        WHERE bs.user_id = pc.user_id
        """
    )
    op.execute(
        "UPDATE pay_cycles SET savings_pct = 0 WHERE savings_pct IS NULL"
    )
    op.execute(
        "UPDATE pay_cycles SET retirement_401k_pct = 0 WHERE retirement_401k_pct IS NULL"
    )
    op.execute("UPDATE pay_cycles SET hsa_amount = 0 WHERE hsa_amount IS NULL")
    op.alter_column("pay_cycles", "savings_pct", existing_type=sa.Numeric(5, 4), nullable=False)
    op.alter_column(
        "pay_cycles", "retirement_401k_pct", existing_type=sa.Numeric(5, 4), nullable=False
    )
    op.alter_column("pay_cycles", "hsa_amount", existing_type=sa.Numeric(12, 2), nullable=False)
