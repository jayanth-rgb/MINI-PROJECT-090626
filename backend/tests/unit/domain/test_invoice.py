"""V2 TC-176..TC-184 — domain.invoice pure arithmetic + invoice_number.

Deterministic unit tests: all inputs and expected outputs come from
sprints/V2/design/test_cases.json verbatim. No time-dependent state.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.domain.invoice import (
    compute_invoice_status,
    compute_invoice_total,
    compute_line_total,
    generate_invoice_number,
)


def test_tc176_compute_line_total_10_x_150_returns_1500():
    assert compute_line_total(10, Decimal("150.00")) == Decimal("1500.00")


def test_tc177_compute_line_total_raises_value_error_when_quantity_zero():
    with pytest.raises(ValueError):
        compute_line_total(0, Decimal("150.00"))


def test_tc178_compute_line_total_raises_value_error_when_unit_price_negative():
    with pytest.raises(ValueError):
        compute_line_total(5, Decimal("-10.00"))


def test_tc179_compute_invoice_total_sums_three_lines_to_350_75():
    total = compute_invoice_total(
        [Decimal("100.00"), Decimal("200.50"), Decimal("50.25")]
    )
    assert total == Decimal("350.75")


def test_tc180_compute_invoice_total_raises_value_error_when_empty_list():
    with pytest.raises(ValueError):
        compute_invoice_total([])


def test_tc181_compute_invoice_status_returns_pending_when_no_payments():
    assert compute_invoice_status(Decimal("1000.00"), []) == "PENDING"


def test_tc182_compute_invoice_status_returns_partial_when_paid_lt_total():
    assert compute_invoice_status(Decimal("1000.00"), [Decimal("400.00")]) == "PARTIAL"


def test_tc183_compute_invoice_status_returns_paid_when_paid_equals_total():
    assert (
        compute_invoice_status(
            Decimal("1000.00"),
            [Decimal("600.00"), Decimal("400.00")],
        )
        == "PAID"
    )


def test_tc184_generate_invoice_number_zero_pads_sales_header_id_to_5_digits():
    result = generate_invoice_number(date(2026, 7, 2), 42)
    assert result == "INV-20260702-00042"
