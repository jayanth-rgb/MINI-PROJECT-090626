"""ST-022 — Payment amount boundary vs invoice total (AC-072 / AC-073).

Seeds an invoice with total_amount=1000.00, then verifies:
  - amount < total -> 201 PARTIAL
  - amount == total -> 201 PAID (single-payment case)
  - amount > total -> 422 (single-payment overpayment)
  - cumulative payments crossing total -> 422 (second-payment overpayment)
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)


def _seed_invoice_total_1000(client, db_session):
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.add(DealerModel(dealer_id=1, dealer_name="Raj Hardwares", place="Mysuru"))
    db_session.add(StaffModel(staff_id=1, staff_name="Chandran"))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1))
    db_session.flush()

    sale_date = (date.today() - timedelta(days=1)).isoformat()
    r_price = client.post(
        "/api/v1/prices",
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "100.00",
            "effective_from": sale_date,
        },
    )
    assert r_price.status_code == 201, r_price.text
    r_sale = client.post(
        "/api/v1/sales",
        json={
            "sales_date": sale_date,
            "dealer_id": 1,
            "loading_staff_id": 1,
            "verified_by_id": 1,
            "lines": [{"design_id": 1, "grade_id": 1, "nos": 10}],
        },
    )
    assert r_sale.status_code == 201, r_sale.text
    sales_header_id = r_sale.json()["header_id"]
    r_inv = client.post("/api/v1/invoices", params={"sales_header_id": sales_header_id})
    assert r_inv.status_code == 201, r_inv.text
    invoice = r_inv.json()
    assert Decimal(invoice["total_amount"]) == Decimal("1000.00")
    return invoice["id"]


@pytest.mark.parametrize("amount,expected_status,expected_state", [
    ("500.00", 201, "PARTIAL"),
    ("1000.00", 201, "PAID"),
    ("1000.01", 422, None),
    ("1500.00", 422, None),
])
def test_st022_single_payment_boundary(
    client, db_session, amount, expected_status, expected_state
):
    invoice_id = _seed_invoice_total_1000(client, db_session)
    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"payment_date": date.today().isoformat(), "amount": amount},
    )
    assert resp.status_code == expected_status, (
        f"amount={amount}: expected {expected_status}, got {resp.status_code}: {resp.text}"
    )
    if expected_state is not None:
        assert resp.json()["status"] == expected_state


def test_st022_cumulative_overpayment_returns_422(client, db_session):
    invoice_id = _seed_invoice_total_1000(client, db_session)
    today = date.today().isoformat()
    r1 = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"payment_date": today, "amount": "600.00"},
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["status"] == "PARTIAL"

    # cumulative would be 600 + 401 = 1001 > 1000
    r2 = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"payment_date": today, "amount": "401.00"},
    )
    assert r2.status_code == 422, (
        f"cumulative overpayment expected 422, got {r2.status_code}: {r2.text}"
    )
