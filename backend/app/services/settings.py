from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.models import BudgetSettings
from app.services.errors import InvalidInput


async def get_settings(session: AsyncSession, user_id: UUID) -> BudgetSettings:
    row = await session.scalar(select(BudgetSettings).where(BudgetSettings.user_id == user_id))
    if row is None:
        # Self-heal in case a user predates the settings row.
        row = BudgetSettings(
            user_id=user_id,
            savings_pct=app_settings.default_savings_pct,
            retirement_401k_pct=app_settings.default_retirement_401k_pct,
            hsa_per_cycle=app_settings.default_hsa_per_cycle,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


def _check_pct(value: Decimal, label: str) -> None:
    if value < 0 or value > 1:
        raise InvalidInput(f"{label} must be between 0 and 1 (e.g. 0.60 for 60%).")


async def update_settings(
    session: AsyncSession,
    user_id: UUID,
    *,
    savings_pct: Decimal | None = None,
    retirement_401k_pct: Decimal | None = None,
    hsa_per_cycle: Decimal | None = None,
) -> BudgetSettings:
    row = await get_settings(session, user_id)

    if savings_pct is not None:
        _check_pct(savings_pct, "Savings percentage")
        row.savings_pct = savings_pct
    if retirement_401k_pct is not None:
        _check_pct(retirement_401k_pct, "401(k) percentage")
        row.retirement_401k_pct = retirement_401k_pct
    if hsa_per_cycle is not None:
        if hsa_per_cycle < 0:
            raise InvalidInput("HSA amount cannot be negative.")
        row.hsa_per_cycle = hsa_per_cycle

    await session.commit()
    await session.refresh(row)
    return row
