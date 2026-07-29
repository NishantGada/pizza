from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class PayCycle(Base, TimestampMixin):
    """One paycheck period. Rule values are snapshotted at creation so a later
    change to BudgetSettings never rewrites the history of past cycles."""

    __tablename__ = "pay_cycles"
    __table_args__ = (UniqueConstraint("user_id", "start_date", "end_date", name="uq_cycle_span"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Post-tax income entered for this cycle.
    income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Snapshot of the applied rules.
    savings_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    retirement_401k_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    hsa_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    user: Mapped["User"] = relationship(back_populates="pay_cycles")  # noqa: F821
    categories: Mapped[list["Category"]] = relationship(  # noqa: F821
        back_populates="pay_cycle", cascade="all, delete-orphan"
    )
