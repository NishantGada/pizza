"""Aggregate already-resolved cycles into the dashboard view.

Pure computation over `(PayCycle, ResolvedCycle)` pairs — no DB access. Keeping
this out of the GraphQL resolver makes the money math independently testable.

For every contribution and category we surface three figures:
* actual   — dollars tracked across the recorded cycles so far
* annual   — a full-year projection (per-cycle average x cycles/year)
* relative — that annual figure prorated to the tracked window (e.g. Jul-Dec),
             i.e. the "should-be" for a year that only started partway through
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models import PayCycle
from app.services.calc import (
    annualize,
    fraction_of_year_from,
    money,
    periods_per_year,
)
from app.services.resolve import ResolvedCycle


@dataclass(frozen=True)
class Projection:
    actual: Decimal
    annual: Decimal
    relative: Decimal


@dataclass(frozen=True)
class CategoryProjection:
    name: str
    cycle_count: int
    projection: Projection


@dataclass(frozen=True)
class DashboardData:
    cycle_count: int
    total_income: Decimal
    total_saved: Decimal
    total_retirement: Decimal
    total_hsa: Decimal
    total_allocated: Decimal
    total_contributed: Decimal
    total_available: Decimal
    saved_projection: Projection
    retirement_projection: Projection
    hsa_projection: Projection
    allocated_projection: Projection
    projection_label: str
    by_category: list[CategoryProjection]


def _empty_projection() -> Projection:
    z = money(Decimal("0"))
    return Projection(actual=z, annual=z, relative=z)


def build_dashboard(resolved: list[tuple[PayCycle, ResolvedCycle]]) -> DashboardData:
    count = len(resolved)
    if count == 0:
        zero = money(Decimal("0"))
        empty = _empty_projection()
        return DashboardData(
            cycle_count=0,
            total_income=zero,
            total_saved=zero,
            total_retirement=zero,
            total_hsa=zero,
            total_allocated=zero,
            total_contributed=zero,
            total_available=zero,
            saved_projection=empty,
            retirement_projection=empty,
            hsa_projection=empty,
            allocated_projection=empty,
            projection_label="",
            by_category=[],
        )

    cycles = [c for c, _ in resolved]
    spans = [(c.end_date - c.start_date).days + 1 for c in cycles]
    ppy = periods_per_year(spans)
    earliest = min(c.start_date for c in cycles)
    fraction = fraction_of_year_from(earliest)
    label = f"{earliest.strftime('%b')}–Dec {earliest.year}"

    def project(total: Decimal, n: int) -> Projection:
        annual = annualize(total, n, ppy)
        return Projection(actual=money(total), annual=annual, relative=money(annual * fraction))

    total_income = sum((r.breakdown.income for _, r in resolved), Decimal("0"))
    total_saved = sum((r.breakdown.savings for _, r in resolved), Decimal("0"))
    total_retirement = sum((r.breakdown.retirement for _, r in resolved), Decimal("0"))
    total_hsa = sum((r.breakdown.hsa for _, r in resolved), Decimal("0"))
    total_allocated = sum((r.breakdown.categories_total for _, r in resolved), Decimal("0"))
    total_available = sum((r.breakdown.available_spending for _, r in resolved), Decimal("0"))
    total_contributed = total_saved + total_retirement + total_hsa + total_allocated

    # Per-category totals across all cycles. A category's own appearance count
    # drives its annualization (ad-hoc rows may show up in only one cycle).
    cat_totals: dict[str, Decimal] = {}
    cat_counts: dict[str, int] = {}
    order: list[str] = []
    for _, r in resolved:
        for cat in r.categories:
            if cat.name not in cat_totals:
                cat_totals[cat.name] = Decimal("0")
                cat_counts[cat.name] = 0
                order.append(cat.name)
            cat_totals[cat.name] += cat.amount
            cat_counts[cat.name] += 1

    by_category = [
        CategoryProjection(
            name=name,
            cycle_count=cat_counts[name],
            projection=project(cat_totals[name], cat_counts[name]),
        )
        for name in order
    ]
    by_category.sort(key=lambda p: (-p.projection.actual, p.name))

    return DashboardData(
        cycle_count=count,
        total_income=money(total_income),
        total_saved=money(total_saved),
        total_retirement=money(total_retirement),
        total_hsa=money(total_hsa),
        total_allocated=money(total_allocated),
        total_contributed=money(total_contributed),
        total_available=money(total_available),
        saved_projection=project(total_saved, count),
        retirement_projection=project(total_retirement, count),
        hsa_projection=project(total_hsa, count),
        allocated_projection=project(total_allocated, count),
        projection_label=label,
        by_category=by_category,
    )
