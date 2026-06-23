"""TC-066 — Sales router (POST /api/v1/sales)."""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def _seed(session):
    dealer = DealerModel(dealer_name="D", place="P")
    loader = StaffModel(staff_name="L")
    verifier = StaffModel(staff_name="V")
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    session.add_all([dealer, loader, verifier, design, grade])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return (
        dealer.dealer_id,
        loader.staff_id,
        verifier.staff_id,
        design.design_id,
        grade.grade_id,
    )


def test_tc066_post_sales_201_decreases_ledger(client, db_session):
    """POST /api/v1/sales returns 201; ledger delta = −nos for each line."""
    dlr_id, ld_id, vf_id, des_id, grd_id = _seed(db_session)
    # Seed +20 inward via the API to set up balance
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(db_session, des_id, grd_id, date.today(), 20, 999, 1)
    db_session.commit()
    resp = client.post(
        "/api/v1/sales",
        json={
            "sales_date": date.today().isoformat(),
            "dealer_id": dlr_id,
            "loading_staff_id": ld_id,
            "verified_by_id": vf_id,
            "lines": [{"design_id": des_id, "grade_id": grd_id, "nos": 5}],
        },
    )
    assert resp.status_code == 201, resp.text
    latest = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=des_id, grade_id=grd_id)
        .order_by(
            StockLedgerModel.txn_date.desc(),
            StockLedgerModel.ledger_id.desc(),
        )
        .first()
    )
    assert latest.delta == -5
    assert latest.running_balance == 15
