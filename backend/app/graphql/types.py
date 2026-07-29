from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

import strawberry

from app.models import BudgetSettings, Category, ContributionCategory, PayCycle, User
from app.services.calc import KIND_FIXED, KIND_PERCENT, category_amount, compute_breakdown, money


@strawberry.enum
class CategoryKind(Enum):
    PERCENT = KIND_PERCENT
    FIXED = KIND_FIXED


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
    id: UUID
    name: str
    kind: CategoryKind
    value: Decimal
    amount: Decimal  # effective dollars for this cycle's income
    created_at: datetime

    @classmethod
    def from_model(cls, c: Category, income: Decimal) -> "CategoryType":
        return cls(
            id=c.id,
            name=c.name,
            kind=CategoryKind(c.kind),
            value=c.value,
            amount=category_amount(income, c.kind, c.value),
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
    def from_model(cls, c: PayCycle) -> "PayCycleType":
        cats = sorted(c.categories, key=lambda x: x.created_at)
        views = [CategoryType.from_model(cat, c.income) for cat in cats]
        cats_total = sum((v.amount for v in views), Decimal("0"))
        breakdown = compute_breakdown(
            income=c.income,
            savings_pct=c.savings_pct,
            retirement_401k_pct=c.retirement_401k_pct,
            hsa_amount=c.hsa_amount,
            categories_total=cats_total,
        )
        return cls(
            id=c.id,
            start_date=c.start_date,
            end_date=c.end_date,
            income=breakdown.income,
            savings_pct=c.savings_pct,
            retirement_401k_pct=c.retirement_401k_pct,
            hsa_amount=breakdown.hsa,
            savings_amount=breakdown.savings,
            retirement_amount=breakdown.retirement,
            categories_total=breakdown.categories_total,
            available_spending=breakdown.available_spending,
            categories=views,
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
