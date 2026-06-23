"""ST-005 — exact 7-day backdate boundary (AC-021)."""
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
from src.presentation.schemas.transactions import InwardCreate, InwardLineCreate


def _seed(session) -> dict:
    supplier = SupplierModel(supplier_name="M", place="Y")
    staff = StaffModel(staff_name="S")
    design = TradingDesignModel(size="16X10", design_name="D")
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


@pytest.mark.parametrize(
    "days_ago, should_pass",
    [
        (7, True),   # boundary inclusive — accepted
        (8, False),  # boundary exclusive — rejected
    ],
)
def test_st005_backdate_window_boundary(db_session, days_ago, should_pass):
    ids = _seed(db_session)
    svc = InwardService(db_session)
    payload = InwardCreate(
        purchase_date=date.today() - timedelta(days=days_ago),
        supplier_id=ids["supplier_id"],
        entered_by_id=ids["staff_id"],
        lines=[
            InwardLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=1
            )
        ],
    )
    if should_pass:
        result = svc.save_inward(payload)
        assert result.header_id is not None
    else:
        with pytest.raises(ValidationError):
            svc.save_inward(payload)
