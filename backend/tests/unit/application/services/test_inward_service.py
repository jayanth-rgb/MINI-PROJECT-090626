"""TC-047, 049, 050, 051, 054, 055, 056 — InwardService (F-007)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.application.services.inward_service import InwardService
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel
from src.presentation.schemas.transactions import InwardCreate, InwardLineCreate


def _seed_inward_world(session) -> dict:
    """Seed supplier, staff, design, grade, and active pair; return ids."""
    supplier = SupplierModel(supplier_name="Manjunatha", place="Mallur")
    staff = StaffModel(staff_name="Chandran")
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_code="1")
    session.add_all([supplier, staff, design, grade])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return {
        "supplier_id": supplier.supplier_id,
        "staff_id": staff.staff_id,
        "design_id": design.design_id,
        "grade_id": grade.grade_id,
    }


def test_tc047_future_purchase_date_raises_validation_error(db_session):
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    payload = InwardCreate(
        purchase_date=date.today() + timedelta(days=1),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_inward(payload)
    assert "future" in exc.value.message.lower()


def test_tc049_purchase_date_older_than_7_days_raises_validation_error(db_session):
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    payload = InwardCreate(
        purchase_date=date.today() - timedelta(days=8),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_inward(payload)
    assert "7 days" in exc.value.message.lower()


def test_tc050_save_inward_snapshots_supplier_place_onto_header(db_session):
    """DS-013 — header.place is the snapshot of supplier.place at save time."""
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    payload = InwardCreate(
        purchase_date=date.today(),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    result = svc.save_inward(payload)
    assert result.place == "Mallur"

    # Mutate the master AFTER save — header place must NOT change
    supplier = db_session.get(SupplierModel, ids["supplier_id"])
    supplier.place = "Belgaum"
    db_session.flush()
    assert result.place == "Mallur"


def test_tc051_inactive_design_grade_pair_raises_validation_error(db_session):
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    # Deactivate the mapping
    pair = (
        db_session.query(DesignGradeMapModel)
        .filter_by(design_id=ids["design_id"], grade_id=ids["grade_id"])
        .one()
    )
    pair.is_active = False
    db_session.flush()
    payload = InwardCreate(
        purchase_date=date.today(),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_inward(payload)
    assert "active mapping" in exc.value.message.lower()


def test_tc054_blank_and_zero_nos_lines_silently_stripped(db_session):
    """RULE-017 — lines with nos == None or 0 are stripped before persist."""
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    grade2 = GradeModel(grade_code="2")
    db_session.add(grade2)
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=ids["design_id"], grade_id=grade2.grade_id)
    )
    db_session.flush()
    payload = InwardCreate(
        purchase_date=date.today(),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=10
            ),
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=grade2.grade_id, nos=0
            ),
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=grade2.grade_id, nos=None
            ),
        ],
    )
    result = svc.save_inward(payload)
    assert len(result.lines) == 1
    assert result.lines[0].nos == 10


def test_tc055_zero_valid_lines_raises_validation_error(db_session):
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    payload = InwardCreate(
        purchase_date=date.today(),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=0
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_inward(payload)
    assert "at least one line" in exc.value.message.lower()


def test_tc056_save_inward_writes_header_lines_and_ledger_atomically(db_session):
    """AC-027 — single transaction commits 1 header + N lines + N ledger rows."""
    svc = InwardService(db_session)
    ids = _seed_inward_world(db_session)
    payload = InwardCreate(
        purchase_date=date.today(),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=7
            )
        ],
    )
    result = svc.save_inward(payload)
    assert result.header_id is not None
    assert len(result.lines) == 1
    # Ledger row exists with delta=+7
    ledger_rows = (
        db_session.query(StockLedgerModel)
        .filter_by(
            design_id=ids["design_id"], grade_id=ids["grade_id"]
        )
        .all()
    )
    assert len(ledger_rows) == 1
    assert ledger_rows[0].delta == 7
    assert ledger_rows[0].running_balance == 7
    assert ledger_rows[0].source_type == "inward"
    assert ledger_rows[0].source_header_id == result.header_id
