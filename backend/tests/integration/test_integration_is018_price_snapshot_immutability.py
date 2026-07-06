"""IS-018 — DF-PriceSnapshot: PATCH /prices AFTER invoice does NOT mutate the invoice.

DS-022 contract: invoice line unit_price is snapshotted at invoice creation and
must never track subsequent PriceMaster edits. Verifies through HTTP round-trip:
create price → sale → invoice → patch price → GET invoice returns OLD price
while GET /prices returns NEW price.
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


def test_is018(client, db_session):
    # ------------------------------------------------------------------ seed master
    design = TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_id=1, grade_code="1")
    dealer = DealerModel(dealer_id=1, dealer_name="Raj Hardwares", place="Mysuru")
    staff = StaffModel(staff_id=1, staff_name="Chandran")
    db_session.add_all([design, grade, dealer, staff])
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1, is_active=True))
    db_session.flush()

    sale_date = (date.today() - timedelta(days=1)).isoformat()

    # STEP 1 — create PriceMaster @ 200.00
    resp_price = client.post(
        "/api/v1/prices",
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "200.00",
            "effective_from": sale_date,
        },
    )
    assert resp_price.status_code == 201, f"POST /prices failed: {resp_price.text}"
    price_id = resp_price.json()["id"]

    # STEP 2 — create Sale (nos=5)
    resp_sale = client.post(
        "/api/v1/sales",
        json={
            "sales_date": sale_date,
            "dealer_id": 1,
            "loading_staff_id": 1,
            "verified_by_id": 1,
            "lines": [{"design_id": 1, "grade_id": 1, "nos": 5}],
        },
    )
    assert resp_sale.status_code == 201, f"POST /sales failed: {resp_sale.text}"
    sales_header_id = resp_sale.json()["header_id"]

    # STEP 3 — create Invoice; expect snapshot @ 200.00 → total 1000.00
    resp_inv = client.post(
        "/api/v1/invoices",
        params={"sales_header_id": sales_header_id},
    )
    assert resp_inv.status_code == 201, f"POST /invoices failed: {resp_inv.text}"
    invoice = resp_inv.json()
    invoice_id = invoice["id"]
    assert Decimal(invoice["total_amount"]) == Decimal("1000.00")
    assert Decimal(invoice["lines"][0]["unit_price"]) == Decimal("200.00")
    assert Decimal(invoice["lines"][0]["line_total"]) == Decimal("1000.00")

    # STEP 4 — PATCH price to 250.00
    resp_patch = client.patch(
        f"/api/v1/prices/{price_id}",
        json={"unit_price": "250.00"},
    )
    assert resp_patch.status_code == 200, f"PATCH price failed: {resp_patch.text}"
    assert Decimal(resp_patch.json()["unit_price"]) == Decimal("250.00")

    # STEP 5 — GET invoice; expect ORIGINAL 200.00 preserved
    resp_get_inv = client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp_get_inv.status_code == 200
    reloaded = resp_get_inv.json()
    assert Decimal(reloaded["total_amount"]) == Decimal("1000.00"), (
        f"total mutated after price PATCH: {reloaded['total_amount']}"
    )
    assert Decimal(reloaded["lines"][0]["unit_price"]) == Decimal("200.00"), (
        f"line unit_price mutated after price PATCH: {reloaded['lines'][0]['unit_price']}"
    )
    assert Decimal(reloaded["lines"][0]["line_total"]) == Decimal("1000.00")

    # STEP 6 — GET /prices confirms master itself did update
    resp_list = client.get("/api/v1/prices")
    assert resp_list.status_code == 200
    matching = [
        p
        for p in resp_list.json()
        if p["id"] == price_id
    ]
    assert len(matching) == 1
    assert Decimal(matching[0]["unit_price"]) == Decimal("250.00"), (
        f"master price should be 250.00, got {matching[0]['unit_price']}"
    )
