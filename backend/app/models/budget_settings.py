from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings as app_settings
from app.db.base import Base, TimestampMixin, new_uuid


class BudgetSettings(Base, TimestampMixin):
    """Per-user, editable budgeting rules. Defaults come from app config."""

    __tablename__ = "budget_settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    savings_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=app_settings.default_savings_pct
    )
    retirement_401k_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=app_settings.default_retirement_401k_pct
    )
    hsa_per_cycle: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=app_settings.default_hsa_per_cycle
    )

    user: Mapped["User"] = relationship(back_populates="settings")  # noqa: F821
