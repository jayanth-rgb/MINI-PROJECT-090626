"""TC-074, 075, 077 — AdjustmentService (F-009)."""
from __future__ import annotations

from datetime import date

import pytest

from src.application.services.adjustment_service import AdjustmentService
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel
from src.presentation.schemas.transactions import (
    AdjustmentCreate,
    AdjustmentLineCreate,
)


def _seed_adj_world(session) -> dict:
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_code="1")
    staff = StaffModel(staff_name="Chandran")
    session.add_all([design, grade, staff])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return {
        "design_id": design.design_id,
        "grade_id": grade.grade_id,
        "staff_id": staff.staff_id,
    }


def test_tc074_difference_equals_physical_minus_software_signed(db_session):
    """AC-038 — difference = physical_cb - software_cb (no abs, can be negative)."""
    svc = AdjustmentService(db_session)
    ids = _seed_adj_world(db_session)
    # Seed +50 via apply_inward → software_cb at adjust time = 50
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(
        db_session, ids["design_id"], ids["grade_id"], date.today(), 50, 1, 1
    )
    db_session.commit()
    payload = AdjustmentCreate(
        stock_date=date.today(),
        entry_date=date.today(),
        design_id=ids["design_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            AdjustmentLineCreate(grade_id=ids["grade_id"], physical_cb=47)
        ],
    )
    result = svc.save_adjustment(payload)
    assert result.lines[0].software_cb == 50
    assert result.lines[0].physical_cb == 47
    assert result.lines[0].difference == -3


def test_tc075_apply_adjustment_writes_ledger_atomic(db_session):
    """AC-039 — ledger row has delta=difference and running_balance = software_cb + difference."""
    svc = AdjustmentService(db_session)
    ids = _seed_adj_world(db_session)
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(
        db_session, ids["design_id"], ids["grade_id"], date.today(), 100, 1, 1
    )
    db_session.commit()
    payload = AdjustmentCreate(
        stock_date=date.today(),
        entry_date=date.today(),
        design_id=ids["design_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            AdjustmentLineCreate(grade_id=ids["grade_id"], physical_cb=120)
        ],
    )
    svc.save_adjustment(payload)
    latest = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=ids["design_id"], grade_id=ids["grade_id"])
        .order_by(
            StockLedgerModel.txn_date.desc(), StockLedgerModel.ledger_id.desc()
        )
        .first()
    )
    assert latest.delta == 20
    assert latest.running_balance == 120
    assert latest.source_type == "adjustment"


def test_tc077_design_with_no_active_grades_raises_err012(db_session):
    """AC-040 / ERR-012 — design without active grade combinations rejects."""
    svc = AdjustmentService(db_session)
    design = TradingDesignModel(size="11X7", design_name="Empty design")
    staff = StaffModel(staff_name="Chandran")
    db_session.add_all([design, staff])
    db_session.flush()
    # No DesignGradeMap rows for this design — ERR-012 trigger
    payload = AdjustmentCreate(
        stock_date=date.today(),
        entry_date=date.today(),
        design_id=design.design_id,
        entered_by_id=staff.staff_id,
        lines=[AdjustmentLineCreate(grade_id=1, physical_cb=10)],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_adjustment(payload)
    assert "no active grade combinations" in exc.value.message.lower()
