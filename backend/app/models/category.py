from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Category(Base, TimestampMixin):
    """A per-cycle contribution row. Two shapes:

    * **Override** (`contribution_category_id` set): overrides one global
      contribution rule for just this cycle. `name` comes from the global rule;
      only `kind`/`value` diverge. At most one override per (cycle, global).
    * **Ad-hoc** (`contribution_category_id` NULL): a one-off category that
      exists only on this cycle. `name` is required.

    A cycle stores a row here only when it diverges from the live globals;
    absence means "inherit the global rule". `kind` is 'percent' (value =
    fraction of income) or 'fixed' (value = dollars); the effective dollar
    amount is derived from the cycle's income at read time.
    """

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("pay_cycle_id", "contribution_category_id", name="uq_cycle_override"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    pay_cycle_id: Mapped[UUID] = mapped_column(
        ForeignKey("pay_cycles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Set -> this row overrides that global rule for this cycle. NULL -> ad-hoc.
    contribution_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("contribution_categories.id", ondelete="CASCADE"), nullable=True
    )

    name: Mapped[str | None] = mapped_column(String(120), nullable=True)  # required for ad-hoc only
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # 'percent' | 'fixed'
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    pay_cycle: Mapped["PayCycle"] = relationship(back_populates="categories")  # noqa: F821
