from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class ContributionCategory(Base, TimestampMixin):
    """A global, per-user contribution rule (e.g. Vacation 5%, Gym $50).

    These are the live rules a user manages once. Each rule is either a
    percent of income (kind='percent', value = fraction like 0.0500) or a
    fixed dollar amount (kind='fixed', value = dollars). Every cycle inherits
    the current set at read time, so editing a rule reflects on all cycles
    instantly; a cycle only stores a `Category` row when it overrides one.
    """

    __tablename__ = "contribution_categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_contrib_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # 'percent' | 'fixed'
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    user: Mapped["User"] = relationship(back_populates="contribution_categories")  # noqa: F821
