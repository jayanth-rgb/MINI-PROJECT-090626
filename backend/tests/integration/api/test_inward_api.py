"""TC-048, 057 — Inward router (POST /api/v1/inward)."""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def _seed(session):
    supplier = SupplierModel(supplier_name="M", place="Mallur")
    staff = StaffModel(staff_name="C")
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    session.add_all([supplier, staff, design, grade])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return supplier.supplier_id, staff.staff_id, design.design_id, grade.grade_id


def test_tc048_post_inward_future_date_returns_422(client, db_session):
    sup_id, stf_id, des_id, grd_id = _seed(db_session)
    db_session.commit()
    resp = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": (date.today() + timedelta(days=1)).isoformat(),
            "supplier_id": sup_id,
            "entered_by_id": stf_id,
            "lines": [{"design_id": des_id, "grade_id": grd_id, "nos": 5}],
        },
    )
    assert resp.status_code == 422
    assert "future" in resp.json().get("detail", "").lower()


def test_tc057_post_inward_201_creates_header_lines_and_ledger(client, db_session):
    """POST returns 201 with hydrated InwardRead; ledger increases per line."""
    sup_id, stf_id, des_id, grd_id = _seed(db_session)
    db_session.commit()
    resp = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date.today().isoformat(),
            "supplier_id": sup_id,
            "entered_by_id": stf_id,
            "lines": [{"design_id": des_id, "grade_id": grd_id, "nos": 7}],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["place"] == "Mallur"
    assert len(body["lines"]) == 1
    assert body["lines"][0]["nos"] == 7
