"""IS-006 — Inward then Sales: ledger decreases by sale nos with Δ=-nos.

Full F-008 flow against a real PostgreSQL via testcontainers.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def test_is006(client, db_session):
    # Seed
    supplier = SupplierModel(supplier_name="Manjunatha", place="Mallur")
    dealer = DealerModel(dealer_name="Raj Hardwares", place="Dindivanam")
    s1 = StaffModel(staff_name="Chandran")
    s2 = StaffModel(staff_name="Jayapal")
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_code="1")
    db_session.add_all([supplier, dealer, s1, s2, design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    db_session.commit()

    # Seed inward of +50 via POST
    resp_inward = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date.today().isoformat(),
            "supplier_id": supplier.supplier_id,
            "entered_by_id": s1.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 50}
            ],
        },
    )
    assert resp_inward.status_code == 201

    # Sale of 12
    resp_sale = client.post(
        "/api/v1/sales",
        json={
            "sales_date": date.today().isoformat(),
            "dealer_id": dealer.dealer_id,
            "loading_staff_id": s1.staff_id,
            "verified_by_id": s2.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 12}
            ],
        },
    )
    assert resp_sale.status_code == 201

    # Verify latest ledger row
    latest = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=design.design_id, grade_id=grade.grade_id)
        .order_by(
            StockLedgerModel.txn_date.desc(),
            StockLedgerModel.ledger_id.desc(),
        )
        .first()
    )
    assert latest.delta == -12
    assert latest.running_balance == 38
    assert latest.source_type == "sale"

    # 2 ledger rows total
    rows = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=design.design_id, grade_id=grade.grade_id)
        .all()
    )
    assert len(rows) == 2
