"""IS-007 — GET /designs/{id}/grades-with-cb → POST /adjustments → ledger reflects signed difference.

Full F-009 flow with DF-003 contract verification.
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
    AdjustmentHeaderModel,
    AdjustmentLineModel,
    StockLedgerModel,
)


def test_is007(client, db_session):
    # Seed
    supplier = SupplierModel(supplier_name="Mfg", place="X")
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

    # Seed balances via inward POST
    client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date.today().isoformat(),
            "supplier_id": supplier.supplier_id,
            "entered_by_id": staff.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": g1.grade_id, "nos": 100},
                {"design_id": design.design_id, "grade_id": g_ob.grade_id, "nos": 50},
            ],
        },
    )

    # GET /designs/{id}/grades-with-cb
    resp_get = client.get(
        f"/api/v1/designs/{design.design_id}/grades-with-cb",
        params={"stock_date": date.today().isoformat()},
    )
    assert resp_get.status_code == 200
    rows = resp_get.json()
    assert len(rows) == 2
    by_code = {r["grade_code"]: r for r in rows}
    assert by_code["1"]["software_cb"] == 100
    assert by_code["OB"]["software_cb"] == 50

    # POST /adjustments: G1 = 95 (Δ=-5), G2 = 50 (Δ=0, skipped at ledger)
    resp_adj = client.post(
        "/api/v1/adjustments",
        json={
            "stock_date": date.today().isoformat(),
            "entry_date": date.today().isoformat(),
            "design_id": design.design_id,
            "entered_by_id": staff.staff_id,
            "lines": [
                {"grade_id": g1.grade_id, "physical_cb": 95},
                {"grade_id": g_ob.grade_id, "physical_cb": 50},
            ],
        },
    )
    assert resp_adj.status_code == 201, resp_adj.text

    # Both adjustment_line rows persisted (audit)
    adj_headers = db_session.query(AdjustmentHeaderModel).all()
    assert len(adj_headers) == 1
    adj_lines = db_session.query(AdjustmentLineModel).all()
    assert len(adj_lines) == 2

    # Ledger: 2 inward + 1 adjustment for G1 only (Δ=-5 for G1; G2 zero-diff skipped)
    ledger = db_session.query(StockLedgerModel).all()
    assert len(ledger) == 3

    # Final running_balance: G1 = 95 (after -5 adjust), G2 = 50 (unchanged)
    latest_g1 = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=design.design_id, grade_id=g1.grade_id)
        .order_by(
            StockLedgerModel.txn_date.desc(),
            StockLedgerModel.ledger_id.desc(),
        )
        .first()
    )
    assert latest_g1.running_balance == 95
    assert latest_g1.source_type == "adjustment"
    assert latest_g1.delta == -5

    latest_g_ob = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=design.design_id, grade_id=g_ob.grade_id)
        .order_by(
            StockLedgerModel.txn_date.desc(),
            StockLedgerModel.ledger_id.desc(),
        )
        .first()
    )
    assert latest_g_ob.running_balance == 50
    assert latest_g_ob.source_type == "inward"  # unchanged
