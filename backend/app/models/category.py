from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Category(Base, TimestampMixin):
    """A per-cycle allocation snapshot deducted from a paycheck.

    Snapshotted from the user's global ContributionCategory rules when a cycle
    is created, but editable per cycle (override the value, skip, or add a
    one-off). `kind` is 'percent' (value = fraction of income) or 'fixed'
    (value = dollars); the effective dollar amount is derived from the cycle's
    income at read time.
    """

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    pay_cycle_id: Mapped[UUID] = mapped_column(
        ForeignKey("pay_cycles.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # 'percent' | 'fixed'
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    pay_cycle: Mapped["PayCycle"] = relationship(back_populates="categories")  # noqa: F821
