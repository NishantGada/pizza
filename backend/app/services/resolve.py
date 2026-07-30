"""Resolve a pay cycle's effective rules from live globals + sparse overrides.

This is the single place that turns "global settings + global contribution
categories + a cycle's overrides" into the concrete numbers shown to the user.
Nothing is snapshotted onto cycles, so editing a global rule reflects on every
cycle the next time it is read.

Resolution rules:
* Settings (savings/401k/HSA): use the cycle's override column if set, else the
  global BudgetSettings value.
* Categories: for each global rule, use the cycle's override row if one exists,
  else inherit the global live. Plus any ad-hoc rows that belong only to the
  cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from app.models import BudgetSettings, ContributionCategory, PayCycle
from app.services.calc import Breakdown, category_amount, compute_breakdown


class CategorySource(str, Enum):
    INHERITED = "inherited"  # straight from the global rule
    OVERRIDE = "override"  # global rule, but this cycle changed the amount
    CYCLE = "cycle"  # ad-hoc, exists only on this cycle


@dataclass(frozen=True)
class ResolvedCategory:
    # Override/ad-hoc row id, or None when the value is inherited live.
    id: UUID | None
    # The global rule this resolves, or None for an ad-hoc cycle-only category.
    contribution_category_id: UUID | None
    name: str
    kind: str
    value: Decimal
    amount: Decimal  # effective dollars for the cycle's income
    source: CategorySource
    created_at: datetime


@dataclass(frozen=True)
class ResolvedCycle:
    savings_pct: Decimal
    retirement_401k_pct: Decimal
    hsa_amount: Decimal
    categories: list[ResolvedCategory]
    breakdown: Breakdown


def resolve_settings(
    cycle: PayCycle, settings: BudgetSettings
) -> tuple[Decimal, Decimal, Decimal]:
    """Effective (savings_pct, retirement_401k_pct, hsa_amount) for a cycle."""
    return (
        cycle.savings_pct if cycle.savings_pct is not None else settings.savings_pct,
        cycle.retirement_401k_pct
        if cycle.retirement_401k_pct is not None
        else settings.retirement_401k_pct,
        cycle.hsa_amount if cycle.hsa_amount is not None else settings.hsa_per_cycle,
    )


def resolve_categories(
    cycle: PayCycle, globals_: list[ContributionCategory]
) -> list[ResolvedCategory]:
    """Effective category list for a cycle: inherited globals, cycle overrides,
    and ad-hoc cycle-only categories. `cycle.categories` must be loaded."""
    overrides = {
        c.contribution_category_id: c
        for c in cycle.categories
        if c.contribution_category_id is not None
    }
    resolved: list[ResolvedCategory] = []

    for g in globals_:
        ov = overrides.get(g.id)
        if ov is not None:
            resolved.append(
                ResolvedCategory(
                    id=ov.id,
                    contribution_category_id=g.id,
                    name=g.name,
                    kind=ov.kind,
                    value=ov.value,
                    amount=category_amount(cycle.income, ov.kind, ov.value),
                    source=CategorySource.OVERRIDE,
                    created_at=g.created_at,
                )
            )
        else:
            resolved.append(
                ResolvedCategory(
                    id=None,
                    contribution_category_id=g.id,
                    name=g.name,
                    kind=g.kind,
                    value=g.value,
                    amount=category_amount(cycle.income, g.kind, g.value),
                    source=CategorySource.INHERITED,
                    created_at=g.created_at,
                )
            )

    adhoc = [c for c in cycle.categories if c.contribution_category_id is None]
    for c in sorted(adhoc, key=lambda x: x.created_at):
        resolved.append(
            ResolvedCategory(
                id=c.id,
                contribution_category_id=None,
                name=c.name or "",
                kind=c.kind,
                value=c.value,
                amount=category_amount(cycle.income, c.kind, c.value),
                source=CategorySource.CYCLE,
                created_at=c.created_at,
            )
        )
    return resolved


def resolve_cycle(
    cycle: PayCycle,
    settings: BudgetSettings,
    globals_: list[ContributionCategory],
) -> ResolvedCycle:
    savings_pct, retirement_401k_pct, hsa_amount = resolve_settings(cycle, settings)
    categories = resolve_categories(cycle, globals_)
    cats_total = sum((c.amount for c in categories), Decimal("0"))
    breakdown = compute_breakdown(
        income=cycle.income,
        savings_pct=savings_pct,
        retirement_401k_pct=retirement_401k_pct,
        hsa_amount=hsa_amount,
        categories_total=cats_total,
    )
    return ResolvedCycle(
        savings_pct=savings_pct,
        retirement_401k_pct=retirement_401k_pct,
        hsa_amount=hsa_amount,
        categories=categories,
        breakdown=breakdown,
    )
