from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class PayCycle(Base, TimestampMixin):
    """One paycheck period.

    A cycle owns only what is genuinely its own: income and date range. The
    applied rules (savings/401k/HSA rates and contribution categories) are
    resolved live from the user's global settings at read time, so editing a
    rule reflects on every cycle instantly. The nullable columns below are
    per-cycle *overrides*: null means "inherit the current global value".
    """

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

    # Per-cycle rule overrides. NULL -> inherit the live global BudgetSettings.
    savings_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    retirement_401k_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    hsa_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    user: Mapped["User"] = relationship(back_populates="pay_cycles")  # noqa: F821
    categories: Mapped[list["Category"]] = relationship(  # noqa: F821
        back_populates="pay_cycle", cascade="all, delete-orphan"
    )
