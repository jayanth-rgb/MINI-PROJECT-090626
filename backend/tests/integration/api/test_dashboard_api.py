"""TC-115, TC-117, TC-118, TC-119, TC-120, TC-130, TC-131, TC-156, TC-159
— Dashboard API integration tests (F-010).

All tests use the `client` fixture (FastAPI TestClient with get_db override)
and `db_session` for seeding. Hits GET /api/v1/dashboard?as_of_date=...
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


# ---------------------------------------------------------------------------
# In-file seed helpers
# ---------------------------------------------------------------------------


def _seed_design(db, name, size):
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, code, is_active=True):
    g = GradeModel(grade_code=code, is_active=is_active)
    db.add(g)
    db.flush()
    return g


def _seed_map(db, design_id, grade_id, is_active=True):
    m = DesignGradeMapModel(design_id=design_id, grade_id=grade_id, is_active=is_active)
    db.add(m)
    db.flush()
    return m


def _seed_ledger(db, design_id, grade_id, txn_date, source_type, delta, running_balance):
    row = StockLedgerModel(
        design_id=design_id,
        grade_id=grade_id,
        txn_date=txn_date,
        source_type=source_type,
        delta=delta,
        running_balance=running_balance,
        source_header_id=1,
        source_line_id=1,
    )
    db.add(row)
    db.flush()
    return row


# ---------------------------------------------------------------------------
# TC-115 — 3 active pairs with ledger movements → 3 rows with all 10 fields
# ---------------------------------------------------------------------------


def test_tc115_three_active_pairs_with_movements(client, db_session):
    """TC-115: DashboardService.list_as_of with 3 active pairs + ledger movements
    returns exactly 3 DashboardRow with all 10 fields populated and correct values."""
    d1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    d2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")
    g3 = _seed_grade(db_session, "2A")

    _seed_map(db_session, d1.design_id, g1.grade_id)
    _seed_map(db_session, d1.design_id, g2.grade_id)
    _seed_map(db_session, d2.design_id, g3.grade_id)

    # Ledger rows per TC-115 spec
    _seed_ledger(db_session, d1.design_id, g1.grade_id, date(2026, 6, 5), "inward", 100, 100)
    _seed_ledger(db_session, d1.design_id, g1.grade_id, date(2026, 6, 10), "sale", -30, 70)
    _seed_ledger(db_session, d1.design_id, g2.grade_id, date(2026, 6, 7), "inward", 50, 50)
    _seed_ledger(db_session, d2.design_id, g3.grade_id, date(2026, 6, 1), "inward", 20, 20)
    _seed_ledger(db_session, d2.design_id, g3.grade_id, date(2026, 6, 8), "adjustment", -5, 15)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200

    body = resp.json()
    assert len(body) == 3

    # All rows must have all 10 required fields
    required_keys = {
        "design_id", "design_name", "size", "grade_id", "grade_code",
        "opening", "inward", "outward", "adjust", "closing"
    }
    for row in body:
        assert required_keys.issubset(row.keys()), f"Missing keys in row: {row.keys()}"

    # Verify sorting and values — ordered by design_name ASC, grade_code ASC
    # 12X8 Ridges/2A, 16X10 Ridges/1, 16X10 Ridges/2
    assert body[0]["design_name"] == "12X8 Ridges" and body[0]["grade_code"] == "2A"
    assert body[0]["opening"] == 0
    assert body[0]["inward"] == 20
    assert body[0]["outward"] == 0
    assert body[0]["adjust"] == -5
    assert body[0]["closing"] == 15

    assert body[1]["design_name"] == "16X10 Ridges" and body[1]["grade_code"] == "1"
    assert body[1]["opening"] == 0
    assert body[1]["inward"] == 100
    assert body[1]["outward"] == 30
    assert body[1]["adjust"] == 0
    assert body[1]["closing"] == 70

    assert body[2]["design_name"] == "16X10 Ridges" and body[2]["grade_code"] == "2"
    assert body[2]["opening"] == 0
    assert body[2]["inward"] == 50
    assert body[2]["outward"] == 0
    assert body[2]["adjust"] == 0
    assert body[2]["closing"] == 50

    # Invariant check: opening + inward - outward + adjust == closing for every row
    for row in body:
        assert row["opening"] + row["inward"] - row["outward"] + row["adjust"] == row["closing"], (
            f"Invariant failed for {row}"
        )


# ---------------------------------------------------------------------------
# TC-117 — S1 seed (6 active pairs), no ledger → 200 with 6 zero rows
# ---------------------------------------------------------------------------


def test_tc117_six_active_pairs_no_ledger_returns_six_zero_rows(client, db_session):
    """TC-117: GET /dashboard?as_of_date=2026-06-15 with 6 active pairs + no ledger
    returns 200 with exactly 6 rows, all numeric columns = 0."""
    d_16x10 = _seed_design(db_session, "16X10 Ridges", "16X10")
    d_12x8 = _seed_design(db_session, "12X8 Ridges", "12X8")
    d_11x7 = _seed_design(db_session, "11X7 Ridges", "11X7")

    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")
    g_ob = _seed_grade(db_session, "OB")

    # 6 active pairs: 16X10{1,2}, 12X8{1,OB}, 11X7{1,2}
    _seed_map(db_session, d_16x10.design_id, g1.grade_id)
    _seed_map(db_session, d_16x10.design_id, g2.grade_id)
    _seed_map(db_session, d_12x8.design_id, g1.grade_id)
    _seed_map(db_session, d_12x8.design_id, g_ob.grade_id)
    _seed_map(db_session, d_11x7.design_id, g1.grade_id)
    _seed_map(db_session, d_11x7.design_id, g2.grade_id)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200

    body = resp.json()
    assert len(body) == 6

    # All zero when no ledger movements
    for row in body:
        assert row["opening"] == 0
        assert row["inward"] == 0
        assert row["outward"] == 0
        assert row["adjust"] == 0
        assert row["closing"] == 0

    # Ordering: design_name ASC, grade_code ASC
    names_grades = [(r["design_name"], r["grade_code"]) for r in body]
    assert names_grades == sorted(names_grades)


# ---------------------------------------------------------------------------
# TC-118 — First month opening is zero (FORMULA-002 base case)
# ---------------------------------------------------------------------------


def test_tc118_first_month_opening_is_zero(client, db_session):
    """TC-118: No rows before 2026-06-01 → opening=0 for as_of=2026-06-30."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # Only a June row — no rows before June 1
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 12), "inward", 40, 40)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-30")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    row = body[0]
    assert row["opening"] == 0
    assert row["inward"] == 40
    assert row["outward"] == 0
    assert row["adjust"] == 0
    assert row["closing"] == 40


# ---------------------------------------------------------------------------
# TC-119 — Opening = Closing of last day of prior month (FORMULA-002)
# ---------------------------------------------------------------------------


def test_tc119_opening_equals_prior_month_closing(client, db_session):
    """TC-119: As-of=2026-06-01 → opening = May 31 closing balance = 75."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # May movements
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 10), "inward", 80, 80)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 20), "sale", -30, 50)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 31), "inward", 25, 75)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-01")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    row = body[0]
    # Opening must equal May 31 closing = 75; no June movements yet → closing=opening
    assert row["opening"] == 75
    assert row["inward"] == 0
    assert row["outward"] == 0
    assert row["adjust"] == 0
    assert row["closing"] == 75


# ---------------------------------------------------------------------------
# TC-120 — Closing = opening + inward - outward + adjust (FORMULA-001)
# ---------------------------------------------------------------------------


def test_tc120_closing_invariant_with_multi_row_june_sequence(client, db_session):
    """TC-120: closing = opening + inward - outward + adjust across mid-month sequence."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # May row sets opening=60
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 31), "inward", 60, 60)
    # June movements
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 3), "inward", 40, 100)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 7), "sale", -25, 75)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 12), "adjustment", 10, 85)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 14), "sale", -5, 80)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    row = body[0]
    assert row["opening"] == 60
    assert row["inward"] == 40
    assert row["outward"] == 30   # 25 + 5
    assert row["adjust"] == 10
    assert row["closing"] == 80
    # Invariant: 60 + 40 - 30 + 10 == 80
    assert row["opening"] + row["inward"] - row["outward"] + row["adjust"] == row["closing"]


# ---------------------------------------------------------------------------
# TC-130 — GET /dashboard with ledger returns 200 + JSON with all 10 keys per row
# ---------------------------------------------------------------------------


def test_tc130_get_dashboard_returns_200_with_correct_schema(client, db_session):
    """TC-130: GET /api/v1/dashboard?as_of_date=2026-06-15 returns 200 +
    JSON array where each row has all 10 required keys."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 5), "inward", 50, 50)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200

    body = resp.json()
    assert len(body) >= 1

    required_keys = {
        "design_id", "design_name", "size", "grade_id", "grade_code",
        "opening", "inward", "outward", "adjust", "closing"
    }
    for row in body:
        assert required_keys.issubset(row.keys())


# ---------------------------------------------------------------------------
# TC-131 — Missing as_of_date → 422
# ---------------------------------------------------------------------------


def test_tc131_missing_as_of_date_returns_422(client, db_session):
    """TC-131: GET /api/v1/dashboard without as_of_date → 422 (required param)."""
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 422
    body = resp.json()
    # FastAPI 422 body contains field info about the missing parameter
    detail_str = str(body)
    assert "as_of_date" in detail_str


# ---------------------------------------------------------------------------
# TC-156 — Back-dated cross-month insert → June dashboard shows correct opening
# ---------------------------------------------------------------------------


def test_tc156_backdated_crossmonth_insert_reflects_in_june_dashboard(client, db_session):
    """TC-156: After back-dated May 30 insert, June opening=65; then June sale of 10
    → outward=10, closing=55. Verifies carry-forward consistency after back-date window."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # Step 1: Insert May 28 row (running_balance=40)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 28), "inward", 40, 40)
    # Step 2: Back-dated May 30 row inserted on June 4 (back-dated 5 days, within 7-day window)
    # After recompute_forward the running_balance for both May rows should be cumulative:
    # May 28: 40, May 30: 65 (40+25)
    # We seed directly with correct running_balance since we're bypassing domain.stock here
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 30), "inward", 25, 65)
    # June 5 sale
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 5), "sale", -10, 55)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    row = body[0]
    # Opening = closing_balance(May 31) = 65 (last May row running_balance)
    assert row["opening"] == 65
    assert row["inward"] == 0
    assert row["outward"] == 10
    assert row["adjust"] == 0
    assert row["closing"] == 55
    # Invariant
    assert row["opening"] + row["inward"] - row["outward"] + row["adjust"] == row["closing"]


# ---------------------------------------------------------------------------
# TC-159 — DI factory smoke: real session wires correctly end-to-end
# ---------------------------------------------------------------------------


def test_tc159_di_factory_smoke_real_session(client, db_session):
    """TC-159: GET /api/v1/dashboard → real PG session via testcontainers.
    Validates get_dashboard_service DI factory wires DashboardService(db) correctly."""
    # Seed one pair with no ledger (simplest smoke scenario)
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)
    db_session.flush()

    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-15")
    assert resp.status_code == 200
    body = resp.json()
    # Must return exactly 1 row for the seeded pair
    assert len(body) == 1
    row = body[0]
    assert row["design_name"] == "16X10 Ridges"
    assert row["grade_code"] == "1"
    # All zero — no ledger rows
    assert row["opening"] == 0
    assert row["closing"] == 0
