from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.services.cycles import get_cycle
from app.services.errors import InvalidInput, NotFound


async def category_totals(
    session: AsyncSession, user_id: UUID
) -> list[tuple[str, Decimal, int]]:
    """Sum each category name across all of the user's pay cycles.

    Returns (name, total_amount, cycle_count) ordered by total desc.
    """
    result = await session.execute(
        select(
            Category.name,
            func.sum(Category.amount),
            func.count(Category.id),
        )
        .where(Category.user_id == user_id)
        .group_by(Category.name)
        .order_by(func.sum(Category.amount).desc(), Category.name.asc())
    )
    return [(name, Decimal(total), int(count)) for name, total, count in result.all()]


async def add_category(
    session: AsyncSession,
    user_id: UUID,
    *,
    pay_cycle_id: UUID,
    name: str,
    amount: Decimal,
) -> Category:
    # Ownership check: raises NotFound if the cycle isn't the user's.
    await get_cycle(session, user_id, pay_cycle_id)
    _validate(name, amount)
    category = Category(
        user_id=user_id,
        pay_cycle_id=pay_cycle_id,
        name=name.strip(),
        amount=amount,
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
    amount: Decimal | None = None,
) -> Category:
    category = await _get_owned(session, user_id, category_id)
    if name is not None:
        if not name.strip():
            raise InvalidInput("Category name cannot be empty.")
        category.name = name.strip()
    if amount is not None:
        if amount < 0:
            raise InvalidInput("Category amount cannot be negative.")
        category.amount = amount
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, user_id: UUID, category_id: UUID) -> None:
    category = await _get_owned(session, user_id, category_id)
    await session.delete(category)
    await session.commit()


def _validate(name: str, amount: Decimal) -> None:
    if not name.strip():
        raise InvalidInput("Category name cannot be empty.")
    if amount < 0:
        raise InvalidInput("Category amount cannot be negative.")
