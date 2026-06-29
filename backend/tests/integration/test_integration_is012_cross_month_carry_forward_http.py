"""IS-012 — F-012 carry-forward end-to-end through HTTP: inward in month X →
GET /dashboard for month X+1 shows opening = closing of month X.

Verifies DS-004 / AC-051 over the full HTTP stack (not just unit-level domain).

Dates are relative to today so the test honors AC-021's 7-day backdate window
on the WRITE side while still spanning a month boundary on the READ side:
  inward_date    = today - 1 day       (within 7-day window)
  dashboard_asof = first_of_next_month_after_inward + 5 days
                                       (deliberately in the NEXT calendar month)

Expected: opening=200 (= closing of inward's month per DS-004), inward=0,
          outward=0, adjust=0, closing=200 in next month's window.
AC-051: opening (month X+1) == closing (month X).
FORMULA-001: 200 + 0 - 0 + 0 == 200.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def _first_of_next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def test_is012(client, db_session):
    # ------------------------------------------------------------------ seed master
    supplier = SupplierModel(supplier_name="Manjunatha", place="Mallur")
    staff = StaffModel(staff_name="Chandran")
    design = TradingDesignModel(design_name="16X10 Ridges", size="16X10", is_active=True)
    grade = GradeModel(grade_code="1", is_active=True)
    db_session.add_all([supplier, staff, design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id, is_active=True)
    )
    db_session.flush()

    # Inward stays within AC-021's 7-day window; dashboard as_of is deliberately
    # placed in the next calendar month relative to the inward, so the dashboard
    # exercises the carry-forward path (opening of new month == closing of old).
    inward_date = date.today() - timedelta(days=1)
    next_month_first = _first_of_next_month(inward_date)
    dashboard_as_of = next_month_first + timedelta(days=5)

    # ------------------------------------------------------------------ inward via HTTP (month X)
    resp_inward = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": inward_date.isoformat(),
            "supplier_id": supplier.supplier_id,
            "entered_by_id": staff.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 200},
            ],
        },
    )
    assert resp_inward.status_code == 201, f"Inward POST failed: {resp_inward.text}"

    # ------------------------------------------------------------------ dashboard via HTTP (month X+1)
    # DashboardService.list_as_of:
    #   month_first = first of dashboard_as_of's month  (= next_month_first)
    #   opening_balance(month_first) → closing_balance(month_first − 1 day) → 200 (DS-004)
    #   sum_deltas_by_source_type(month_first, dashboard_as_of) → empty (no rows in X+1)
    #   closing_balance(dashboard_as_of) → 200 (latest_as_of returns inward row)
    resp_dash = client.get(f"/api/v1/dashboard?as_of_date={dashboard_as_of.isoformat()}")
    assert resp_dash.status_code == 200, f"Dashboard GET failed: {resp_dash.text}"

    body = resp_dash.json()
    assert len(body) == 1, f"Expected 1 dashboard row, got {len(body)}: {body}"
    row = body[0]

    # Identity fields
    assert row["design_name"] == "16X10 Ridges"
    assert row["grade_code"] == "1"

    # AC-051: opening (month X+1) == closing (month X) == 200
    assert row["opening"] == 200, (
        f"AC-051: Expected opening=200 (= prior-month closing per DS-004), got {row['opening']}"
    )
    assert row["inward"]  == 0, f"Expected inward=0 in month X+1, got {row['inward']}"
    assert row["outward"] == 0, f"Expected outward=0 in month X+1, got {row['outward']}"
    assert row["adjust"]  == 0, f"Expected adjust=0 in month X+1, got {row['adjust']}"
    assert row["closing"] == 200, (
        f"Expected closing=200 (carry-forward from month X), got {row['closing']}"
    )

    # FORMULA-001 (server-asserted; verify client-side too).
    invariant = row["opening"] + row["inward"] - row["outward"] + row["adjust"]
    assert invariant == row["closing"], (
        f"FORMULA-001 violated: {row['opening']} + {row['inward']} - {row['outward']} "
        f"+ {row['adjust']} = {invariant} != {row['closing']}"
    )

    # AC-051 explicit semantic check: zero current-month movements → closing == opening.
    assert row["closing"] == row["opening"], (
        f"AC-051: With zero current-month movements, closing ({row['closing']}) "
        f"must equal opening ({row['opening']})"
    )
