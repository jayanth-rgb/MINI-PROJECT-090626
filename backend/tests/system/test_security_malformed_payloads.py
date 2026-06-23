"""ST-006 — Defense-in-depth: malformed POST /api/v1/inward payloads rejected at boundary."""
from __future__ import annotations

from datetime import date

import pytest

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import InwardHeaderModel


@pytest.fixture
def seeded_ids(db_session):
    supplier = SupplierModel(supplier_name="M", place="Y")
    staff = StaffModel(staff_name="S")
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    db_session.add_all([supplier, staff, design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    db_session.commit()
    return {
        "supplier_id": supplier.supplier_id,
        "staff_id": staff.staff_id,
        "design_id": design.design_id,
        "grade_id": grade.grade_id,
    }


@pytest.mark.parametrize(
    "malformation, expected_substring",
    [
        ({"nos": "abc"}, "valid"),
        ({"missing_field": "supplier_id"}, "supplier_id"),
        ({"nos": -1}, "greater than"),
    ],
)
def test_st006_malformed_inward_payloads_rejected_with_422(
    client, db_session, seeded_ids, malformation, expected_substring
):
    """Pydantic intercepts before service; no DB write occurs."""
    base = {
        "purchase_date": date.today().isoformat(),
        "supplier_id": seeded_ids["supplier_id"],
        "entered_by_id": seeded_ids["staff_id"],
        "lines": [
            {
                "design_id": seeded_ids["design_id"],
                "grade_id": seeded_ids["grade_id"],
                "nos": 5,
            }
        ],
    }
    # Apply malformation
    if "missing_field" in malformation:
        # Remove the named field to test required-field validation
        base.pop(malformation["missing_field"], None)
    elif "nos" in malformation:
        base["lines"][0]["nos"] = malformation["nos"]

    resp = client.post("/api/v1/inward", json=base)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    # No InwardHeader row should have been created
    headers = db_session.query(InwardHeaderModel).all()
    assert len(headers) == 0, "Malformed payload leaked a header row"
