"""IS-005 — POST /api/v1/inward → service → repo → domain.apply_inward → ledger.

Full F-007 data flow against a real PostgreSQL via testcontainers.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    InwardHeaderModel,
    InwardLineModel,
    StockLedgerModel,
)


def test_is005(client, db_session):
    # Seed masters
    supplier = SupplierModel(supplier_name="Manjunatha", place="Mallur")
    staff = StaffModel(staff_name="Chandran")
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    g1 = GradeModel(grade_code="1")
    g_ob = GradeModel(grade_code="OB")
    db_session.add_all([supplier, staff, design, g1, g_ob])
    db_session.flush()
    db_session.add_all([
        DesignGradeMapModel(design_id=design.design_id, grade_id=g1.grade_id),
        DesignGradeMapModel(design_id=design.design_id, grade_id=g_ob.grade_id),
    ])
    db_session.commit()

    resp = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date.today().isoformat(),
            "supplier_id": supplier.supplier_id,
            "entered_by_id": staff.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": g1.grade_id, "nos": 10},
                {"design_id": design.design_id, "grade_id": g_ob.grade_id, "nos": 5},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["place"] == "Mallur"  # DS-013 snapshot
    assert len(body["lines"]) == 2

    # Header row exists
    headers = db_session.query(InwardHeaderModel).all()
    assert len(headers) == 1
    assert headers[0].place == "Mallur"
    assert headers[0].supplier_id == supplier.supplier_id

    # Line rows exist
    lines = db_session.query(InwardLineModel).all()
    assert len(lines) == 2

    # Ledger rows exist with correct deltas + running_balances
    ledger = db_session.query(StockLedgerModel).order_by(StockLedgerModel.ledger_id).all()
    assert len(ledger) == 2
    by_grade = {row.grade_id: row for row in ledger}
    assert by_grade[g1.grade_id].delta == 10
    assert by_grade[g1.grade_id].running_balance == 10
    assert by_grade[g1.grade_id].source_type == "inward"
    assert by_grade[g_ob.grade_id].delta == 5
    assert by_grade[g_ob.grade_id].running_balance == 5
