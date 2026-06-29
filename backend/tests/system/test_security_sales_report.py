"""TC-149, TC-158 — Security tests for GET /api/v1/reports/sales (F-011).

TC-149: invalid date_from=not-a-date → 422 (FastAPI date parse rejection).
TC-158: SQL injection attempt via places=' OR 1=1-- → 200, zero rows
        (SQLAlchemy .in_() parameter binding; literal string matches no place).
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DealerModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    SalesHeaderModel,
    SalesLineModel,
)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_staff(db):
    loader = StaffModel(staff_name="Loader A")
    verifier = StaffModel(staff_name="Verifier B")
    db.add_all([loader, verifier])
    db.flush()
    return loader.staff_id, verifier.staff_id


def _seed_sale(db, sales_date, dealer_id, place_snapshot, loader_id, verifier_id, lines):
    header = SalesHeaderModel(
        sales_date=sales_date,
        dealer_id=dealer_id,
        place=place_snapshot,
        loading_staff_id=loader_id,
        verified_by_id=verifier_id,
    )
    db.add(header)
    db.flush()
    for ln in lines:
        sl = SalesLineModel(
            header_id=header.header_id,
            design_id=ln["design_id"],
            grade_id=ln["grade_id"],
            nos=ln["nos"],
        )
        db.add(sl)
    db.flush()
    return header


# ---------------------------------------------------------------------------
# TC-149: invalid date param → HTTP 422
# ---------------------------------------------------------------------------

def test_tc149_invalid_date_from_returns_422(client):
    """GET /api/v1/reports/sales?date_from=not-a-date returns HTTP 422.

    FastAPI rejects the request at the boundary before reaching the service.
    PRD non_functional.security: server-side input validation.
    """
    resp = client.get("/api/v1/reports/sales?date_from=not-a-date")
    assert resp.status_code == 422, (
        f"Expected 422 for invalid date_from, got {resp.status_code}: {resp.text}"
    )

    # FastAPI validation error body must mention the offending parameter
    body = resp.json()
    detail_str = str(body)
    assert "date_from" in detail_str, (
        f"Expected 'date_from' in validation error detail, got: {detail_str}"
    )


# ---------------------------------------------------------------------------
# TC-158: SQL injection via places param → 200 with zero matching rows
# ---------------------------------------------------------------------------

def test_tc158_sql_injection_via_places_returns_empty(client, db_session):
    """GET /reports/sales?places=' OR 1=1-- → 200, transaction_row_count=0.

    SQLAlchemy .in_() uses parameter binding — the literal string
    "' OR 1=1--" is treated as a value to match exactly, not executed as SQL.
    No real place has this value, so zero rows are returned. No 500.
    """
    # Seed a real sale so there IS data in the DB — injection attempt must still
    # return zero rows (not all rows, which is what a successful injection would do).
    loader_id, verifier_id = _seed_staff(db_session)
    dealer = DealerModel(dealer_name="Raj Hardwares", place="Dindivanam", is_active=True)
    db_session.add(dealer)
    db_session.flush()
    design = TradingDesignModel(design_name="16X10 Ridges", size="16X10", is_active=True)
    grade = GradeModel(grade_code="1", is_active=True)
    db_session.add_all([design, grade])
    db_session.flush()

    _seed_sale(
        db_session, date(2026, 6, 15), dealer.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 10}],
    )

    # SQL injection attempt — URL-encoded single quote and OR clause
    injection_payload = "' OR 1=1--"
    resp = client.get(f"/api/v1/reports/sales?places={injection_payload}")

    # Must not crash (no 500)
    assert resp.status_code == 200, (
        f"Expected 200 for SQL injection attempt, got {resp.status_code}: {resp.text}"
    )

    body = resp.json()
    transactions = body["transactions"]

    # SQLAlchemy parameter binding must mean NO rows match the injection string
    # as a literal place value — verifies no SQL injection occurred.
    assert len(transactions) == 0, (
        f"Expected 0 transactions for SQL injection payload (place literal not matched), "
        f"got {len(transactions)} rows — possible SQL injection vulnerability!"
    )
    # Also verify consolidation is empty (reconciliation invariant still holds)
    assert len(body["consolidation"]) == 0, (
        f"Expected 0 consolidation rows for SQL injection payload, "
        f"got {len(body['consolidation'])}"
    )
