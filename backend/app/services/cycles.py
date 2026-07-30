from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PayCycle
from app.services.errors import InvalidInput, NotFound


async def list_cycles(session: AsyncSession, user_id: UUID) -> list[PayCycle]:
    result = await session.scalars(
        select(PayCycle)
        .where(PayCycle.user_id == user_id)
        .options(selectinload(PayCycle.categories))
        .order_by(PayCycle.start_date.desc())
    )
    return list(result)


async def get_cycle(session: AsyncSession, user_id: UUID, cycle_id: UUID) -> PayCycle:
    cycle = await session.scalar(
        select(PayCycle)
        .where(PayCycle.id == cycle_id, PayCycle.user_id == user_id)
        .options(selectinload(PayCycle.categories))
    )
    if cycle is None:
        raise NotFound("Pay cycle not found.")
    return cycle


async def create_cycle(
    session: AsyncSession,
    user_id: UUID,
    *,
    start_date: date,
    end_date: date,
    income: Decimal,
) -> PayCycle:
    if end_date < start_date:
        raise InvalidInput("End date must be on or after the start date.")
    if income < 0:
        raise InvalidInput("Income cannot be negative.")

    # A cycle owns only income + dates. Rules (settings and contribution
    # categories) are inherited live from the user's globals at read time, so a
    # new cycle starts with no overrides.
    cycle = PayCycle(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        income=income,
    )
    session.add(cycle)
    await session.commit()
    return await get_cycle(session, user_id, cycle.id)


async def update_cycle(
    session: AsyncSession,
    user_id: UUID,
    cycle_id: UUID,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    income: Decimal | None = None,
) -> PayCycle:
    cycle = await get_cycle(session, user_id, cycle_id)
    new_start = start_date if start_date is not None else cycle.start_date
    new_end = end_date if end_date is not None else cycle.end_date
    if new_end < new_start:
        raise InvalidInput("End date must be on or after the start date.")
    if income is not None:
        if income < 0:
            raise InvalidInput("Income cannot be negative.")
        cycle.income = income
    cycle.start_date = new_start
    cycle.end_date = new_end
    await session.commit()
    return await get_cycle(session, user_id, cycle_id)


async def delete_cycle(session: AsyncSession, user_id: UUID, cycle_id: UUID) -> None:
    cycle = await get_cycle(session, user_id, cycle_id)
    await session.delete(cycle)
    await session.commit()
