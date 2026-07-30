"""Per-cycle contribution rows: overrides of a global rule, or ad-hoc extras.

A cycle inherits the live global contribution categories. It only stores a row
here when it diverges: an *override* (custom amount for one global rule in this
cycle) or an *ad-hoc* category (exists only on this cycle). Everything else is
resolved live in `app.services.resolve`.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, ContributionCategory
from app.services.calc import KIND_FIXED, KIND_PERCENT
from app.services.cycles import get_cycle
from app.services.errors import InvalidInput, NotFound

# --- Overrides of a global rule for a single cycle ------------------------


async def set_override(
    session: AsyncSession,
    user_id: UUID,
    *,
    pay_cycle_id: UUID,
    contribution_category_id: UUID,
    kind: str,
    value: Decimal,
) -> None:
    """Override a global contribution rule for just this cycle (upsert)."""
    await get_cycle(session, user_id, pay_cycle_id)  # ownership check
    await _get_owned_global(session, user_id, contribution_category_id)  # ownership check
    _validate(kind, value)
    row = await session.scalar(
        select(Category).where(
            Category.pay_cycle_id == pay_cycle_id,
            Category.contribution_category_id == contribution_category_id,
        )
    )
    if row is None:
        session.add(
            Category(
                user_id=user_id,
                pay_cycle_id=pay_cycle_id,
                contribution_category_id=contribution_category_id,
                kind=kind,
                value=value,
            )
        )
    else:
        row.kind = kind
        row.value = value
    await session.commit()


async def clear_override(
    session: AsyncSession,
    user_id: UUID,
    *,
    pay_cycle_id: UUID,
    contribution_category_id: UUID,
) -> None:
    """Drop a cycle's override so it inherits the global rule again."""
    await get_cycle(session, user_id, pay_cycle_id)  # ownership check
    row = await session.scalar(
        select(Category).where(
            Category.user_id == user_id,
            Category.pay_cycle_id == pay_cycle_id,
            Category.contribution_category_id == contribution_category_id,
        )
    )
    if row is not None:
        await session.delete(row)
        await session.commit()


# --- Ad-hoc categories that exist only on one cycle -----------------------


async def add_adhoc(
    session: AsyncSession,
    user_id: UUID,
    *,
    pay_cycle_id: UUID,
    name: str,
    kind: str,
    value: Decimal,
) -> Category:
    await get_cycle(session, user_id, pay_cycle_id)  # ownership check
    name = _clean_name(name)
    _validate(kind, value)
    row = Category(
        user_id=user_id,
        pay_cycle_id=pay_cycle_id,
        contribution_category_id=None,
        name=name,
        kind=kind,
        value=value,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_adhoc(
    session: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    *,
    name: str | None = None,
    kind: str | None = None,
    value: Decimal | None = None,
) -> Category:
    row = await _get_owned_adhoc(session, user_id, category_id)
    new_kind = kind if kind is not None else row.kind
    new_value = value if value is not None else row.value
    if kind is not None or value is not None:
        _validate(new_kind, new_value)
        row.kind = new_kind
        row.value = new_value
    if name is not None:
        row.name = _clean_name(name)
    await session.commit()
    await session.refresh(row)
    return row


async def delete_adhoc(session: AsyncSession, user_id: UUID, category_id: UUID) -> UUID:
    """Delete an ad-hoc category. Returns its pay cycle id for view rebuilds."""
    row = await _get_owned_adhoc(session, user_id, category_id)
    pay_cycle_id = row.pay_cycle_id
    await session.delete(row)
    await session.commit()
    return pay_cycle_id


# --- Helpers --------------------------------------------------------------


async def _get_owned_global(
    session: AsyncSession, user_id: UUID, category_id: UUID
) -> ContributionCategory:
    row = await session.scalar(
        select(ContributionCategory).where(
            ContributionCategory.id == category_id,
            ContributionCategory.user_id == user_id,
        )
    )
    if row is None:
        raise NotFound("Contribution category not found.")
    return row


async def _get_owned_adhoc(
    session: AsyncSession, user_id: UUID, category_id: UUID
) -> Category:
    row = await session.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if row is None:
        raise NotFound("Category not found.")
    if row.contribution_category_id is not None:
        raise InvalidInput("This category is an override; edit it via the global rule instead.")
    return row


def _clean_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidInput("Category name cannot be empty.")
    return cleaned


def _validate(kind: str, value: Decimal) -> None:
    if kind not in (KIND_PERCENT, KIND_FIXED):
        raise InvalidInput("Category kind must be 'percent' or 'fixed'.")
    if value < 0:
        raise InvalidInput("Category value cannot be negative.")
    if kind == KIND_PERCENT and value > 1:
        raise InvalidInput("Percentage must be between 0 and 1 (e.g. 0.05 for 5%).")
