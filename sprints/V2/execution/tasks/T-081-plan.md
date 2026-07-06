# T-081 — `domain/invoice.py` — pure invoice arithmetic functions

**Module:** M-011 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Pure domain layer — no SQLAlchemy, no HTTP, no I/O. Mirrors `domain/stock.py` (S2) isolation. DS-022: `compute_line_total` and `compute_invoice_total` use `Decimal` arithmetic with explicit 2dp rounding (ROUND_HALF_UP) to prevent floating-point drift in financial calculations. DS-023: `generate_invoice_number` is deterministic — same inputs always produce the same number.

## Implementation logic

```python
# backend/src/domain/invoice.py
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
```

## Constraints

- `compute_line_total`: `ValueError` on `quantity <= 0` OR `unit_price < 0` (not `< 0` for unit_price — `0` is valid per DS-022 zero-price fallback).
- `compute_invoice_total`: `ValueError` on empty list — an invoice with no lines is invalid.
- `compute_invoice_status`: `paid_sum == 0` → PENDING. This uses `paid_sum <= 0` check to defend against negative payment edge case, but `PaymentCreate.amount` has `gt=0` validator so negatives won't reach the DB.
- `generate_invoice_number`: zero-pads `sales_header_id` to 5 digits exactly. Format: `INV-YYYYMMDD-NNNNN`.
- All `Decimal` inputs arrive from SQLAlchemy `Numeric` columns — already `Decimal` type, no casting needed.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `python -c "from src.domain.invoice import compute_line_total, generate_invoice_number; from decimal import Decimal; from datetime import date; print(compute_line_total(10, Decimal('150')), generate_invoice_number(date(2026,7,2), 42))"` → `1500.00 INV-20260702-00042`
- **Automated**: TC-176..TC-184 unit tests pass (no DB needed).
- **DoD**: 4 functions exported. ValueError on invalid inputs. All Decimal returns quantized to 2dp. generate_invoice_number deterministic and zero-padded.

## Checkout

> *"domain/invoice.py created. 4 pure functions: compute_line_total, compute_invoice_total, compute_invoice_status, generate_invoice_number. TC-176..TC-184 covered. Ready for T-084 (InvoiceService)."*
