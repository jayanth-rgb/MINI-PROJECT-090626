"""ST-024 — Second POST /invoices for same sales_header_id returns 409 (AC-070)."""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)


def test_st024_duplicate_invoice_returns_409(client, db_session):
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
            "lines": [{"design_id": 1, "grade_id": 1, "nos": 5}],
        },
    )
    assert r_sale.status_code == 201, r_sale.text
    sales_header_id = r_sale.json()["header_id"]

    first = client.post("/api/v1/invoices", params={"sales_header_id": sales_header_id})
    assert first.status_code == 201, f"first invoice failed: {first.text}"

    dup = client.post("/api/v1/invoices", params={"sales_header_id": sales_header_id})
    assert dup.status_code == 409, (
        f"duplicate invoice expected 409, got {dup.status_code}: {dup.text}"
    )
    assert "Traceback" not in dup.text
