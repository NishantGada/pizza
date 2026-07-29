from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, PayCycle
from app.services.calc import KIND_FIXED, KIND_PERCENT, category_amount
from app.services.cycles import get_cycle
from app.services.errors import InvalidInput, NotFound


async def category_totals(
    session: AsyncSession, user_id: UUID
) -> list[tuple[str, Decimal, int]]:
    """Sum each category name across all of the user's pay cycles.

    Percent categories resolve to their effective dollars for the cycle they
    belong to, so this aggregates real contributed amounts. Returns
    (name, total_amount, cycle_count) ordered by total desc.
    """
    result = await session.scalars(
        select(PayCycle)
        .where(PayCycle.user_id == user_id)
        .options(selectinload(PayCycle.categories))
    )
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for cycle in result:
        for cat in cycle.categories:
            amount = category_amount(cycle.income, cat.kind, cat.value)
            totals[cat.name] = totals.get(cat.name, Decimal("0")) + amount
            counts[cat.name] = counts.get(cat.name, 0) + 1
    rows = [(name, total, counts[name]) for name, total in totals.items()]
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


async def add_category(
    session: AsyncSession,
    user_id: UUID,
    *,
    pay_cycle_id: UUID,
    name: str,
    kind: str,
    value: Decimal,
) -> Category:
    # Ownership check: raises NotFound if the cycle isn't the user's.
    await get_cycle(session, user_id, pay_cycle_id)
    name = _clean_name(name)
    _validate(kind, value)
    category = Category(
        user_id=user_id,
        pay_cycle_id=pay_cycle_id,
        name=name,
        kind=kind,
        value=value,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def _get_owned(session: AsyncSession, user_id: UUID, category_id: UUID) -> Category:
    category = await session.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if category is None:
        raise NotFound("Category not found.")
    return category


async def update_category(
    session: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    *,
    name: str | None = None,
    kind: str | None = None,
    value: Decimal | None = None,
) -> Category:
    category = await _get_owned(session, user_id, category_id)
    new_kind = kind if kind is not None else category.kind
    new_value = value if value is not None else category.value
    if kind is not None or value is not None:
        _validate(new_kind, new_value)
        category.kind = new_kind
        category.value = new_value
    if name is not None:
        category.name = _clean_name(name)
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, user_id: UUID, category_id: UUID) -> None:
    category = await _get_owned(session, user_id, category_id)
    await session.delete(category)
    await session.commit()


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
