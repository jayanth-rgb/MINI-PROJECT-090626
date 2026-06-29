"""ST-010 — SQL injection protection for GET /api/v1/reports/sales (F-011).

Extends TC-158 to cover ALL THREE list-type filters:
  1. dealer_ids  (list[int])  — non-int payload → FastAPI rejects with 422
  2. design_ids  (list[int])  — non-int payload → FastAPI rejects with 422
  3. places      (list[str])  — free-form string; SQLAlchemy .in_() parameter
                                binding treats it as a literal value → 200 + 0 rows

Post-loop assertion: tbl_sales_header still contains the seeded row,
confirming no DROP TABLE was executed.

PRD non_functional.security: all inputs validated server-side.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import text

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
# Seed helpers (inlined)
# ---------------------------------------------------------------------------

def _seed_staff(db):
    loader = StaffModel(staff_name="ST010 Loader")
    verifier = StaffModel(staff_name="ST010 Verifier")
    db.add_all([loader, verifier])
    db.flush()
    return loader.staff_id, verifier.staff_id


def _seed_dealer(db, name: str, place: str) -> DealerModel:
    d = DealerModel(dealer_name=name, place=place, is_active=True)
    db.add(d)
    db.flush()
    return d


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


def test_st010(client, db_session):
    """ST-010: SQL injection protection across all 3 list-type filters of /reports/sales."""
    # ------------------------------------------------------------------
    # Seed minimal data: 1 dealer, 1 sale (place="Mysuru") with 1 line
    # ------------------------------------------------------------------
    loader_id, verifier_id = _seed_staff(db_session)
    dealer = _seed_dealer(db_session, "ST010 Dealer", "Mysuru")
    design = TradingDesignModel(design_name="ST010 Design", size="16X10", is_active=True)
    grade = GradeModel(grade_code="ST10-1", is_active=True)
    db_session.add_all([design, grade])
    db_session.flush()

    seeded_header = _seed_sale(
        db_session,
        date.today() - __import__("datetime").timedelta(days=1),
        dealer.dealer_id,
        "Mysuru",
        loader_id,
        verifier_id,
        [{"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 5}],
    )
    seeded_header_id = seeded_header.header_id

    # ------------------------------------------------------------------
    # Injection test table (matches system_test_scenarios.json spec)
    # ------------------------------------------------------------------
    # Each entry: (param, payload, expected_status, check_empty_body)
    injections = [
        # dealer_ids is list[int] — non-int string rejected at FastAPI Query parse
        (
            "dealer_ids",
            "1; DROP TABLE tbl_sales_header;--",
            422,
            False,
        ),
        # design_ids is list[int] — subquery string rejected at FastAPI Query parse
        (
            "design_ids",
            "(SELECT design_id FROM tbl_trading_design)",
            422,
            False,
        ),
        # places is list[str] — SQLAlchemy .in_() binds as literal value → 200, 0 rows
        (
            "places",
            "'; DROP TABLE tbl_sales_header;--",
            200,
            True,  # transactions=[] and consolidation=[]
        ),
    ]

    for param, payload, expected_status, check_empty_body in injections:
        resp = client.get(f"/api/v1/reports/sales?{param}={payload}")

        assert resp.status_code == expected_status, (
            f"ST-010 FAIL [{param}={payload!r}]: "
            f"expected HTTP {expected_status}, got {resp.status_code}. "
            f"Body: {resp.text}"
        )

        if check_empty_body:
            body = resp.json()
            transactions = body.get("transactions", [])
            consolidation = body.get("consolidation", [])
            assert len(transactions) == 0, (
                f"ST-010 FAIL [places injection]: expected 0 transactions, "
                f"got {len(transactions)} — possible SQL injection!"
            )
            assert len(consolidation) == 0, (
                f"ST-010 FAIL [places injection]: expected 0 consolidation rows, "
                f"got {len(consolidation)} — possible SQL injection!"
            )

    # ------------------------------------------------------------------
    # Post-loop: tbl_sales_header must still exist and contain the seeded row
    # Confirms the DROP TABLE attempts were NOT executed.
    # ------------------------------------------------------------------
    count_result = db_session.execute(
        text("SELECT COUNT(*) FROM tbl_sales_header WHERE header_id = :hid"),
        {"hid": seeded_header_id},
    ).scalar()

    assert count_result == 1, (
        f"ST-010 FAIL: tbl_sales_header does not contain seeded header_id={seeded_header_id} "
        f"after injection attempts — table may have been dropped or row deleted! "
        f"count={count_result}"
    )
