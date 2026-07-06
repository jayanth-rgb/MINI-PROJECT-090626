"""V2 TC-217 — POST /invoices creates an invoice from a sales order (SUPERVISOR only).

Router takes sales_header_id as a query parameter (DS-023 on-demand pattern).
invoice_number's YYYYMMDD segment is derived from date.today() at creation time,
so we assert the semantic invariants: prefix, sales_header_id suffix, total,
status, and line count — not the exact date segment (would be non-deterministic).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.pricing import PriceMasterModel
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel

from tests.integration.v2._helpers import bearer, seed_staff, seed_user


def test_tc217_create_invoice_returns_201_with_invoice_read(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.add(DealerModel(dealer_id=1, dealer_name="Raj Hardwares", place="Dindivanam"))
    seed_staff(db_session)
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1))
    db_session.add(
        PriceMasterModel(
            design_id=1,
            grade_id=1,
            unit_price=Decimal("90.00"),
            effective_from=date(2026, 1, 1),
            is_active=True,
        )
    )
    db_session.add(
        SalesHeaderModel(
            header_id=5,
            sales_date=date(2026, 7, 1),
            dealer_id=1,
            place="Dindivanam",
            loading_staff_id=1,
            verified_by_id=1,
        )
    )
    db_session.flush()
    db_session.add(
        SalesLineModel(
            line_id=10,
            header_id=5,
            design_id=1,
            grade_id=1,
            nos=20,
        )
    )
    db_session.flush()

    resp = client.post(
        "/api/v1/invoices",
        params={"sales_header_id": 5},
        headers=bearer("admin", "SUPERVISOR"),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["invoice_number"].startswith("INV-")
    assert body["invoice_number"].endswith("-00005")
    assert Decimal(body["total_amount"]) == Decimal("1800.00")
    assert body["status"] == "PENDING"
    assert len(body["lines"]) == 1
