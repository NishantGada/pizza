from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

import strawberry

from app.models import BudgetSettings, ContributionCategory, PayCycle, User
from app.services.calc import KIND_FIXED, KIND_PERCENT
from app.services.resolve import CategorySource, ResolvedCategory, ResolvedCycle


@strawberry.enum
class CategoryKind(Enum):
    PERCENT = KIND_PERCENT
    FIXED = KIND_FIXED


@strawberry.enum
class CategorySourceType(Enum):
    INHERITED = CategorySource.INHERITED.value
    OVERRIDE = CategorySource.OVERRIDE.value
    CYCLE = CategorySource.CYCLE.value


@strawberry.type
class UserType:
    id: UUID
    email: str
    created_at: datetime

    @classmethod
    def from_model(cls, u: User) -> "UserType":
        return cls(id=u.id, email=u.email, created_at=u.created_at)


@strawberry.type
class AuthPayload:
    token: str
    user: UserType


@strawberry.type
class BudgetSettingsType:
    id: UUID
    savings_pct: Decimal
    retirement_401k_pct: Decimal
    hsa_per_cycle: Decimal

    @classmethod
    def from_model(cls, s: BudgetSettings) -> "BudgetSettingsType":
        return cls(
            id=s.id,
            savings_pct=s.savings_pct,
            retirement_401k_pct=s.retirement_401k_pct,
            hsa_per_cycle=s.hsa_per_cycle,
        )


@strawberry.type
class ContributionCategoryType:
    id: UUID
    name: str
    kind: CategoryKind
    value: Decimal
    created_at: datetime

    @classmethod
    def from_model(cls, c: ContributionCategory) -> "ContributionCategoryType":
        return cls(
            id=c.id,
            name=c.name,
            kind=CategoryKind(c.kind),
            value=c.value,
            created_at=c.created_at,
        )


@strawberry.type
class CategoryType:
    # Present only when the cycle stores a row (override or ad-hoc); null when
    # the value is inherited live from the global rule.
    id: UUID | None
    contribution_category_id: UUID | None
    name: str
    kind: CategoryKind
    value: Decimal
    amount: Decimal  # effective dollars for this cycle's income
    source: CategorySourceType
    created_at: datetime

    @classmethod
    def from_resolved(cls, c: ResolvedCategory) -> "CategoryType":
        return cls(
            id=c.id,
            contribution_category_id=c.contribution_category_id,
            name=c.name,
            kind=CategoryKind(c.kind),
            value=c.value,
            amount=c.amount,
            source=CategorySourceType(c.source.value),
            created_at=c.created_at,
        )


@strawberry.type
class PayCycleType:
    id: UUID
    start_date: date
    end_date: date
    income: Decimal
    savings_pct: Decimal
    retirement_401k_pct: Decimal
    hsa_amount: Decimal
    savings_amount: Decimal
    retirement_amount: Decimal
    categories_total: Decimal
    available_spending: Decimal
    categories: list[CategoryType]

    @classmethod
    def from_resolved(cls, c: PayCycle, r: ResolvedCycle) -> "PayCycleType":
        return cls(
            id=c.id,
            start_date=c.start_date,
            end_date=c.end_date,
            income=r.breakdown.income,
            savings_pct=r.savings_pct,
            retirement_401k_pct=r.retirement_401k_pct,
            hsa_amount=r.breakdown.hsa,
            savings_amount=r.breakdown.savings,
            retirement_amount=r.breakdown.retirement,
            categories_total=r.breakdown.categories_total,
            available_spending=r.breakdown.available_spending,
            categories=[CategoryType.from_resolved(rc) for rc in r.categories],
        )


@strawberry.type
class CategoryTotal:
    name: str
    total: Decimal
    cycle_count: int


@strawberry.type
class DashboardSummary:
    cycle_count: int
    total_income: Decimal
    total_saved: Decimal
    total_retirement: Decimal
    total_hsa: Decimal
    total_allocated: Decimal
    total_contributed: Decimal
    total_available: Decimal
    latest_cycle: PayCycleType | None
    by_category: list[CategoryTotal]
