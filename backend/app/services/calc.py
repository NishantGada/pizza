from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")
DAYS_PER_YEAR = Decimal("365.25")

# Category kinds. 'percent' -> value is a fraction of income; 'fixed' -> value is dollars.
KIND_PERCENT = "percent"
KIND_FIXED = "fixed"


def money(value: Decimal) -> Decimal:
    """Round to cents, half-up."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def category_amount(income: Decimal, kind: str, value: Decimal) -> Decimal:
    """Effective dollar amount of a category for a given cycle income."""
    if kind == KIND_PERCENT:
        return money(Decimal(income) * Decimal(value))
    return money(Decimal(value))


def periods_per_year(spans_days: list[int]) -> Decimal:
    """Estimate how many pay cycles fit in a year from observed cycle spans.

    Averages the given spans and divides a calendar year by that average, so
    biweekly cycles (~14 days) yield ~26, semimonthly (~15) ~24, etc.
    """
    valid = [s for s in spans_days if s > 0]
    if not valid:
        return Decimal("0")
    avg = Decimal(sum(valid)) / Decimal(len(valid))
    return DAYS_PER_YEAR / avg


def fraction_of_year_from(start: date) -> Decimal:
    """Fraction of the calendar year covered by [start, Dec 31] inclusive.

    Used to prorate a full-year projection down to "the part of the year we
    actually track" (e.g. July–December ≈ 0.504).
    """
    year_end = date(start.year, 12, 31)
    total_days = Decimal((year_end - date(start.year, 1, 1)).days + 1)
    window_days = Decimal((year_end - start).days + 1)
    return window_days / total_days


def annualize(total: Decimal, cycle_count: int, periods_per_year_: Decimal) -> Decimal:
    """Project a per-cycle average out to a full year's worth of cycles."""
    if cycle_count <= 0:
        return money(Decimal("0"))
    return money((Decimal(total) / Decimal(cycle_count)) * periods_per_year_)


@dataclass(frozen=True)
class Breakdown:
    income: Decimal
    savings: Decimal
    retirement: Decimal
    hsa: Decimal
    categories_total: Decimal
    available_spending: Decimal


def compute_breakdown(
    *,
    income: Decimal,
    savings_pct: Decimal,
    retirement_401k_pct: Decimal,
    hsa_amount: Decimal,
    categories_total: Decimal,
) -> Breakdown:
    """All deductions apply to the entered post-tax income.

    available_spending = income - savings - 401k - hsa - sum(categories)
    """
    savings = money(income * savings_pct)
    retirement = money(income * retirement_401k_pct)
    hsa = money(hsa_amount)
    cats = money(categories_total)
    available = money(income - savings - retirement - hsa - cats)
    return Breakdown(
        income=money(income),
        savings=savings,
        retirement=retirement,
        hsa=hsa,
        categories_total=cats,
        available_spending=available,
    )
