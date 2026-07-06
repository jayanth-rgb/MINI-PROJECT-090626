"""IS-014 — DF-Invoice: S2 sale → V2 invoice → V2 payments — full lifecycle.

Covers the composed HTTP path:
  POST /prices → POST /sales → POST /invoices?sales_header_id
   → POST /invoices/{id}/payments (partial) → GET (PARTIAL)
   → POST /invoices/{id}/payments (rest)    → GET (PAID)
   → POST /invoices duplicate → 409
   → POST /invoices/{id}/payments overpayment → 422

Uses today-1 for the sales date to stay within AC-021's 7-day backdate window
across all run dates. Uses the default client fixture's SUPERVISOR JWT so
SUPERVISOR-only write endpoints (POST /prices, POST /invoices,
POST /invoices/{id}/payments) are unlocked.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)


def test_is014(client, db_session):
    # ------------------------------------------------------------------ seed master
    design = TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_id=1, grade_code="1")
    dealer = DealerModel(dealer_id=1, dealer_name="Raj Hardwares", place="Mysuru")
    staff = StaffModel(staff_id=1, staff_name="Chandran")
    db_session.add_all([design, grade, dealer, staff])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=1, grade_id=1, is_active=True)
    )
    db_session.flush()

    sale_date = (date.today() - timedelta(days=1)).isoformat()
    today_iso = date.today().isoformat()

    # ---------------------------------------------- STEP 1 — create PriceMaster row
    resp_price = client.post(
        "/api/v1/prices",
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "150.00",
            "effective_from": sale_date,
        },
    )
    assert resp_price.status_code == 201, f"POST /prices failed: {resp_price.text}"

    # ---------------------------------------------- STEP 2 — create Sale
    resp_sale = client.post(
        "/api/v1/sales",
        json={
            "sales_date": sale_date,
            "dealer_id": 1,
            "loading_staff_id": 1,
            "verified_by_id": 1,
            "lines": [{"design_id": 1, "grade_id": 1, "nos": 10}],
        },
    )
    assert resp_sale.status_code == 201, f"POST /sales failed: {resp_sale.text}"
    sales_header_id = resp_sale.json()["header_id"]

    # ---------------------------------------------- STEP 3 — create Invoice (PENDING)
    resp_inv = client.post(
        "/api/v1/invoices",
        params={"sales_header_id": sales_header_id},
    )
    assert resp_inv.status_code == 201, f"POST /invoices failed: {resp_inv.text}"
    invoice = resp_inv.json()
    invoice_id = invoice["id"]
    assert invoice["status"] == "PENDING"
    assert Decimal(invoice["total_amount"]) == Decimal("1500.00")
    assert len(invoice["lines"]) == 1
    line = invoice["lines"][0]
    assert Decimal(line["unit_price"]) == Decimal("150.00")
    assert line["quantity"] == 10
    assert Decimal(line["line_total"]) == Decimal("1500.00")

    # ---------------------------------------------- STEP 4 — partial payment → PARTIAL
    resp_p1 = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={
            "payment_date": today_iso,
            "amount": "600.00",
            "notes": "first tranche",
        },
    )
    assert resp_p1.status_code == 201, f"partial payment failed: {resp_p1.text}"
    body_p1 = resp_p1.json()
    assert body_p1["status"] == "PARTIAL"
    assert len(body_p1["payments"]) == 1
    assert Decimal(body_p1["payments"][0]["amount"]) == Decimal("600.00")

    # ---------------------------------------------- STEP 5 — GET confirms PARTIAL
    resp_g1 = client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp_g1.status_code == 200
    body_g1 = resp_g1.json()
    assert body_g1["status"] == "PARTIAL"
    assert sum(Decimal(p["amount"]) for p in body_g1["payments"]) == Decimal("600.00")
    assert Decimal(body_g1["total_amount"]) == Decimal("1500.00")

    # ---------------------------------------------- STEP 6 — final payment → PAID
    resp_p2 = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={
            "payment_date": today_iso,
            "amount": "900.00",
            "notes": None,
        },
    )
    assert resp_p2.status_code == 201, f"final payment failed: {resp_p2.text}"
    body_p2 = resp_p2.json()
    assert body_p2["status"] == "PAID"
    assert len(body_p2["payments"]) == 2

    # ---------------------------------------------- STEP 7 — GET confirms PAID
    resp_g2 = client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp_g2.status_code == 200
    body_g2 = resp_g2.json()
    assert body_g2["status"] == "PAID"
    assert sum(Decimal(p["amount"]) for p in body_g2["payments"]) == Decimal("1500.00")

    # ---------------------------------------------- STEP 8 — duplicate invoice → 409
    resp_dup = client.post(
        "/api/v1/invoices",
        params={"sales_header_id": sales_header_id},
    )
    assert resp_dup.status_code == 409, (
        f"duplicate invoice should return 409, got {resp_dup.status_code}: {resp_dup.text}"
    )

    # ---------------------------------------------- STEP 9 — overpayment → 422
    resp_over = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={
            "payment_date": today_iso,
            "amount": "1.00",
            "notes": None,
        },
    )
    assert resp_over.status_code == 422, (
        f"overpayment should return 422, got {resp_over.status_code}: {resp_over.text}"
    )
