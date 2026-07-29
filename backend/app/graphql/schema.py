from collections.abc import Awaitable
from datetime import date
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

import strawberry
from graphql import GraphQLError

from app.core.security import create_access_token
from app.graphql.context import require_user
from app.graphql.types import (
    AuthPayload,
    BudgetSettingsType,
    CategoryKind,
    CategoryTotal,
    CategoryType,
    ContributionCategoryType,
    DashboardSummary,
    PayCycleType,
    UserType,
)
from app.services import auth, categories, contributions, cycles, settings
from app.services.calc import money
from app.services.errors import ServiceError

T = TypeVar("T")


async def guard(coro: Awaitable[T]) -> T:
    try:
        return await coro
    except ServiceError as exc:
        raise GraphQLError(str(exc)) from exc


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    async def me(self, info: strawberry.Info) -> UserType:
        user_id = require_user(info)
        async with info.context.db() as session:
            user = await guard(auth.get_user(session, user_id))
            if user is None:
                raise GraphQLError("User not found.")
            return UserType.from_model(user)

    @strawberry.field
    async def budget_settings(self, info: strawberry.Info) -> BudgetSettingsType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(settings.get_settings(session, user_id))
            return BudgetSettingsType.from_model(row)

    @strawberry.field
    async def contribution_categories(
        self, info: strawberry.Info
    ) -> list[ContributionCategoryType]:
        user_id = require_user(info)
        async with info.context.db() as session:
            rows = await guard(contributions.list_contribution_categories(session, user_id))
            return [ContributionCategoryType.from_model(r) for r in rows]

    @strawberry.field
    async def pay_cycles(self, info: strawberry.Info) -> list[PayCycleType]:
        user_id = require_user(info)
        async with info.context.db() as session:
            rows = await guard(cycles.list_cycles(session, user_id))
            return [PayCycleType.from_model(c) for c in rows]

    @strawberry.field
    async def pay_cycle(self, info: strawberry.Info, id: UUID) -> PayCycleType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(cycles.get_cycle(session, user_id, id))
            return PayCycleType.from_model(row)

    @strawberry.field
    async def dashboard(self, info: strawberry.Info) -> DashboardSummary:
        user_id = require_user(info)
        async with info.context.db() as session:
            rows = await guard(cycles.list_cycles(session, user_id))
            views = [PayCycleType.from_model(c) for c in rows]
            cat_totals = await guard(categories.category_totals(session, user_id))
        total_saved = money(sum((v.savings_amount for v in views), Decimal("0")))
        total_retirement = money(sum((v.retirement_amount for v in views), Decimal("0")))
        total_hsa = money(sum((v.hsa_amount for v in views), Decimal("0")))
        total_allocated = money(sum((v.categories_total for v in views), Decimal("0")))
        return DashboardSummary(
            cycle_count=len(views),
            total_income=money(sum((v.income for v in views), Decimal("0"))),
            total_saved=total_saved,
            total_retirement=total_retirement,
            total_hsa=total_hsa,
            total_allocated=total_allocated,
            total_contributed=money(total_saved + total_retirement + total_hsa + total_allocated),
            total_available=money(sum((v.available_spending for v in views), Decimal("0"))),
            latest_cycle=views[0] if views else None,
            by_category=[
                CategoryTotal(name=name, total=money(total), cycle_count=count)
                for name, total, count in cat_totals
            ],
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def register(self, info: strawberry.Info, email: str, password: str) -> AuthPayload:
        async with info.context.db() as session:
            user = await guard(auth.register(session, email, password))
            return AuthPayload(
                token=create_access_token(str(user.id)), user=UserType.from_model(user)
            )

    @strawberry.mutation
    async def login(self, info: strawberry.Info, email: str, password: str) -> AuthPayload:
        async with info.context.db() as session:
            user = await guard(auth.authenticate(session, email, password))
            return AuthPayload(
                token=create_access_token(str(user.id)), user=UserType.from_model(user)
            )

    @strawberry.mutation
    async def update_budget_settings(
        self,
        info: strawberry.Info,
        savings_pct: Decimal | None = None,
        retirement_401k_pct: Decimal | None = None,
        hsa_per_cycle: Decimal | None = None,
    ) -> BudgetSettingsType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                settings.update_settings(
                    session,
                    user_id,
                    savings_pct=savings_pct,
                    retirement_401k_pct=retirement_401k_pct,
                    hsa_per_cycle=hsa_per_cycle,
                )
            )
            return BudgetSettingsType.from_model(row)

    @strawberry.mutation
    async def add_contribution_category(
        self,
        info: strawberry.Info,
        name: str,
        kind: CategoryKind,
        value: Decimal,
    ) -> ContributionCategoryType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                contributions.add_contribution_category(
                    session, user_id, name=name, kind=kind.value, value=value
                )
            )
            return ContributionCategoryType.from_model(row)

    @strawberry.mutation
    async def update_contribution_category(
        self,
        info: strawberry.Info,
        id: UUID,
        name: str | None = None,
        kind: CategoryKind | None = None,
        value: Decimal | None = None,
    ) -> ContributionCategoryType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                contributions.update_contribution_category(
                    session,
                    user_id,
                    id,
                    name=name,
                    kind=kind.value if kind is not None else None,
                    value=value,
                )
            )
            return ContributionCategoryType.from_model(row)

    @strawberry.mutation
    async def delete_contribution_category(self, info: strawberry.Info, id: UUID) -> bool:
        user_id = require_user(info)
        async with info.context.db() as session:
            await guard(contributions.delete_contribution_category(session, user_id, id))
            return True

    @strawberry.mutation
    async def create_pay_cycle(
        self,
        info: strawberry.Info,
        start_date: date,
        end_date: date,
        income: Decimal,
    ) -> PayCycleType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                cycles.create_cycle(
                    session,
                    user_id,
                    start_date=start_date,
                    end_date=end_date,
                    income=income,
                )
            )
            return PayCycleType.from_model(row)

    @strawberry.mutation
    async def update_pay_cycle(
        self,
        info: strawberry.Info,
        id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        income: Decimal | None = None,
    ) -> PayCycleType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                cycles.update_cycle(
                    session,
                    user_id,
                    id,
                    start_date=start_date,
                    end_date=end_date,
                    income=income,
                )
            )
            return PayCycleType.from_model(row)

    @strawberry.mutation
    async def delete_pay_cycle(self, info: strawberry.Info, id: UUID) -> bool:
        user_id = require_user(info)
        async with info.context.db() as session:
            await guard(cycles.delete_cycle(session, user_id, id))
            return True

    @strawberry.mutation
    async def add_category(
        self,
        info: strawberry.Info,
        pay_cycle_id: UUID,
        name: str,
        kind: CategoryKind,
        value: Decimal,
    ) -> CategoryType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                categories.add_category(
                    session,
                    user_id,
                    pay_cycle_id=pay_cycle_id,
                    name=name,
                    kind=kind.value,
                    value=value,
                )
            )
            cycle = await guard(cycles.get_cycle(session, user_id, pay_cycle_id))
            return CategoryType.from_model(row, cycle.income)

    @strawberry.mutation
    async def update_category(
        self,
        info: strawberry.Info,
        id: UUID,
        name: str | None = None,
        kind: CategoryKind | None = None,
        value: Decimal | None = None,
    ) -> CategoryType:
        user_id = require_user(info)
        async with info.context.db() as session:
            row = await guard(
                categories.update_category(
                    session,
                    user_id,
                    id,
                    name=name,
                    kind=kind.value if kind is not None else None,
                    value=value,
                )
            )
            cycle = await guard(cycles.get_cycle(session, user_id, row.pay_cycle_id))
            return CategoryType.from_model(row, cycle.income)

    @strawberry.mutation
    async def delete_category(self, info: strawberry.Info, id: UUID) -> bool:
        user_id = require_user(info)
        async with info.context.db() as session:
            await guard(categories.delete_category(session, user_id, id))
            return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
