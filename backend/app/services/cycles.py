from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, PayCycle
from app.services.contributions import list_contribution_categories
from app.services.errors import InvalidInput, NotFound
from app.services.settings import get_settings


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

    # Snapshot current rule values so future settings changes never rewrite history.
    rules = await get_settings(session, user_id)
    templates = await list_contribution_categories(session, user_id)
    cycle = PayCycle(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        income=income,
        savings_pct=rules.savings_pct,
        retirement_401k_pct=rules.retirement_401k_pct,
        hsa_amount=rules.hsa_per_cycle,
    )
    # Snapshot the user's global contribution categories onto this cycle.
    cycle.categories = [
        Category(user_id=user_id, name=t.name, kind=t.kind, value=t.value) for t in templates
    ]
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
