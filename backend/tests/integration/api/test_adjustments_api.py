"""TC-076, 078 — Adjustments router (POST /api/v1/adjustments)."""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def _seed_with_active_pair(session):
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    staff = StaffModel(staff_name="S")
    session.add_all([design, grade, staff])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return design.design_id, grade.grade_id, staff.staff_id


def test_tc076_post_adjustment_201_balance_equals_physical_cb(client, db_session):
    """After save, latest ledger row's running_balance == physical_cb."""
    des_id, grd_id, stf_id = _seed_with_active_pair(db_session)
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(db_session, des_id, grd_id, date.today(), 100, 999, 1)
    db_session.commit()
    resp = client.post(
        "/api/v1/adjustments",
        json={
            "stock_date": date.today().isoformat(),
            "entry_date": date.today().isoformat(),
            "design_id": des_id,
            "entered_by_id": stf_id,
            "lines": [{"grade_id": grd_id, "physical_cb": 120}],
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
    assert latest.running_balance == 120


def test_tc078_post_adjustment_design_without_active_grades_returns_422(client, db_session):
    """ERR-012 — design with no active grade combinations → 422."""
    design = TradingDesignModel(size="11X7", design_name="Empty design")
    staff = StaffModel(staff_name="S")
    db_session.add_all([design, staff])
    db_session.commit()
    resp = client.post(
        "/api/v1/adjustments",
        json={
            "stock_date": date.today().isoformat(),
            "entry_date": date.today().isoformat(),
            "design_id": design.design_id,
            "entered_by_id": staff.staff_id,
            "lines": [{"grade_id": 1, "physical_cb": 10}],
        },
    )
    assert resp.status_code == 422
    assert "active grade combinations" in resp.json().get("detail", "").lower()
