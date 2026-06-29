"""IS-011 — S2→S3 cross-sprint flow: POST /inward + POST /sales + POST /adjustments
via S2 stack → GET /dashboard via S3 stack reflects all 3 movement types.

ALL writes go through real HTTP POST (FastAPI TestClient → real router →
real service → real domain.stock → real testcontainers PG).
Master data seeded via SQLAlchemy (ORM is acceptable for master CRUD).
No direct domain.stock calls in the test body — the cross-sprint contract is
that S3 reads correctly aggregate what S2 writes produce.

Dates are relative to today (date.today() - 1 day for all txns; dashboard
as_of_date = today) so the test survives across run dates while still honoring
AC-021's 7-day backdate window enforced by InwardService.

Cumulative invariant: 100 inward − 30 sale − 5 adjustment = 65 closing.
Per-movement attribution depends on whether the txn date and as_of_date sit in
the same month (today.day > 1) or straddle a month boundary (today.day == 1).
Both cases satisfy FORMULA-001.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def test_is011(client, db_session):
    # ------------------------------------------------------------------ seed master via ORM
    supplier = SupplierModel(supplier_name="Manjunatha", place="Mallur")
    # 2 staff: one for inward entry + sales loading/verify, one for verify
    s1 = StaffModel(staff_name="Chandran")
    s2 = StaffModel(staff_name="Jayapal")
    dealer = DealerModel(dealer_name="Raj Hardwares", place="Mysuru")
    design = TradingDesignModel(design_name="16X10 Ridges", size="16X10", is_active=True)
    grade = GradeModel(grade_code="1", is_active=True)
    db_session.add_all([supplier, s1, s2, dealer, design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id, is_active=True)
    )
    db_session.flush()

    # Date arithmetic: keep every txn within AC-021's 7-day backdate window so
    # InwardService accepts the POST regardless of today's date.
    today = date.today()
    txn_date = today - timedelta(days=1)  # 1 day back — same calendar month as today
                                          # unless today.day == 1 (handled in assert below).
    txn_date_iso = txn_date.isoformat()
    as_of_iso = today.isoformat()

    # ------------------------------------------------------------------ S2 WRITE PATH (real HTTP)
    # Step 1: POST /inward — nos=100 → ledger delta=+100 running=100
    resp_inward = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": txn_date_iso,
            "supplier_id": supplier.supplier_id,
            "entered_by_id": s1.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 100},
            ],
        },
    )
    assert resp_inward.status_code == 201, f"Inward POST failed: {resp_inward.text}"

    # Step 2: POST /sales — nos=30 → ledger delta=-30 running=70
    resp_sale = client.post(
        "/api/v1/sales",
        json={
            "sales_date": txn_date_iso,
            "dealer_id": dealer.dealer_id,
            "loading_staff_id": s1.staff_id,
            "verified_by_id": s2.staff_id,
            "lines": [
                {"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 30},
            ],
        },
    )
    assert resp_sale.status_code == 201, f"Sales POST failed: {resp_sale.text}"

    # Step 3: POST /adjustments — physical_cb=65 → diff = 65 - 70 = -5 → running=65
    resp_adj = client.post(
        "/api/v1/adjustments",
        json={
            "stock_date": txn_date_iso,
            "entry_date": txn_date_iso,
            "design_id": design.design_id,
            "entered_by_id": s1.staff_id,
            "lines": [
                {"grade_id": grade.grade_id, "physical_cb": 65},
            ],
        },
    )
    assert resp_adj.status_code == 201, f"Adjustment POST failed: {resp_adj.text}"

    # ------------------------------------------------------------------ S3 READ PATH (real HTTP)
    resp_dash = client.get(f"/api/v1/dashboard?as_of_date={as_of_iso}")
    assert resp_dash.status_code == 200, f"Dashboard GET failed: {resp_dash.text}"

    body = resp_dash.json()
    assert len(body) == 1, f"Expected 1 dashboard row, got {len(body)}: {body}"
    row = body[0]

    # Identity fields
    assert row["design_name"] == "16X10 Ridges"
    assert row["grade_code"] == "1"

    # Per-movement attribution depends on whether txn_date is in same month as today.
    # Either case satisfies FORMULA-001 and produces closing=65.
    txn_in_current_month = (
        txn_date.year == today.year and txn_date.month == today.month
    )
    if txn_in_current_month:
        expected = {"opening": 0, "inward": 100, "outward": 30, "adjust": -5}
    else:
        # today.day == 1 case: all 3 txns landed in previous month, so they're
        # already absorbed into the opening balance for current month.
        expected = {"opening": 65, "inward": 0, "outward": 0, "adjust": 0}

    assert row["opening"] == expected["opening"], (
        f"Expected opening={expected['opening']} (txn_in_current_month={txn_in_current_month}), "
        f"got {row['opening']}"
    )
    assert row["inward"] == expected["inward"], f"Expected inward={expected['inward']}, got {row['inward']}"
    assert row["outward"] == expected["outward"], f"Expected outward={expected['outward']}, got {row['outward']}"
    assert row["adjust"] == expected["adjust"], f"Expected adjust={expected['adjust']}, got {row['adjust']}"

    # Cumulative invariant: closing always == 65, regardless of month split.
    assert row["closing"] == 65, f"Expected closing=65, got {row['closing']}"

    # FORMULA-001 must hold in both cases.
    invariant = row["opening"] + row["inward"] - row["outward"] + row["adjust"]
    assert invariant == row["closing"], (
        f"FORMULA-001 violated: {row['opening']} + {row['inward']} - {row['outward']} "
        f"+ {row['adjust']} = {invariant} != {row['closing']}"
    )
