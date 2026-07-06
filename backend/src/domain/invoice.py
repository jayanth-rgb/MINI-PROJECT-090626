from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal


_TWO_PLACES = Decimal("0.01")


def compute_line_total(quantity: int, unit_price: Decimal) -> Decimal:
    if quantity <= 0:
        raise ValueError(f"quantity must be > 0, got {quantity}")
    if unit_price < 0:
        raise ValueError(f"unit_price must be >= 0, got {unit_price}")
    return (Decimal(quantity) * unit_price).quantize(_TWO_PLACES, ROUND_HALF_UP)


def compute_invoice_total(line_totals: list[Decimal]) -> Decimal:
    if not line_totals:
        raise ValueError("line_totals must not be empty")
    return sum(line_totals, Decimal("0")).quantize(_TWO_PLACES, ROUND_HALF_UP)


def compute_invoice_status(
    total_amount: Decimal,
    paid_amounts: list[Decimal],
) -> Literal["PENDING", "PARTIAL", "PAID"]:
    paid_sum = sum(paid_amounts, Decimal("0"))
    if paid_sum <= 0:
        return "PENDING"
    if paid_sum >= total_amount:
        return "PAID"
    return "PARTIAL"


def generate_invoice_number(invoice_date: date, sales_header_id: int) -> str:
    return f"INV-{invoice_date.strftime('%Y%m%d')}-{sales_header_id:05d}"
