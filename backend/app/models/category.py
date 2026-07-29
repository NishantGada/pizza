from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Category(Base, TimestampMixin):
    """A user-defined allocation (fitness, vacation, ...) deducted from a cycle."""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    pay_cycle_id: Mapped[UUID] = mapped_column(
        ForeignKey("pay_cycles.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    pay_cycle: Mapped["PayCycle"] = relationship(back_populates="categories")  # noqa: F821
