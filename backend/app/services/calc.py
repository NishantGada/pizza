from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Round to cents, half-up."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


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
