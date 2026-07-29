"""Global, per-user contribution categories (the reusable templates).

These are managed once (e.g. "Vacation 5%", "Education 10%", "Gym $50") and
snapshotted onto each new pay cycle by `cycles.create_cycle`.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContributionCategory
from app.services.calc import KIND_FIXED, KIND_PERCENT
from app.services.errors import Conflict, InvalidInput, NotFound


async def list_contribution_categories(
    session: AsyncSession, user_id: UUID
) -> list[ContributionCategory]:
    result = await session.scalars(
        select(ContributionCategory)
        .where(ContributionCategory.user_id == user_id)
        .order_by(ContributionCategory.created_at.asc())
    )
    return list(result)


async def add_contribution_category(
    session: AsyncSession,
    user_id: UUID,
    *,
    name: str,
    kind: str,
    value: Decimal,
) -> ContributionCategory:
    name = _clean_name(name)
    _validate(kind, value)
    row = ContributionCategory(user_id=user_id, name=name, kind=kind, value=value)
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict(f"A contribution category named “{name}” already exists.") from exc
    await session.refresh(row)
    return row


async def _get_owned(
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


async def update_contribution_category(
    session: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    *,
    name: str | None = None,
    kind: str | None = None,
    value: Decimal | None = None,
) -> ContributionCategory:
    row = await _get_owned(session, user_id, category_id)
    new_kind = kind if kind is not None else row.kind
    new_value = value if value is not None else row.value
    if kind is not None or value is not None:
        _validate(new_kind, new_value)
        row.kind = new_kind
        row.value = new_value
    if name is not None:
        row.name = _clean_name(name)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict(f"A contribution category named “{row.name}” already exists.") from exc
    await session.refresh(row)
    return row


async def delete_contribution_category(
    session: AsyncSession, user_id: UUID, category_id: UUID
) -> None:
    row = await _get_owned(session, user_id, category_id)
    await session.delete(row)
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
