"""TC-116, TC-121, TC-127, TC-128, TC-129 — DashboardService unit + edge tests (F-010).

These tests exercise DashboardService.list_as_of against a real PostgreSQL
container (testcontainers via db_session) because the service touches both the
DesignGradeMapRepository and LedgerAggregatesRepository — both of which require
PG. Edge cases are co-located here per project convention (no separate _edge.py).
"""
from __future__ import annotations

import pytest
from datetime import date

from src.application.services.dashboard_service import DashboardService
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


# ---------------------------------------------------------------------------
# In-file seed helpers (NOT added to conftest.py per instructions)
# ---------------------------------------------------------------------------


def _seed_design(db, design_id, name, size):
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, grade_code):
    g = GradeModel(grade_code=grade_code, is_active=True)
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
# TC-116 — Edge: empty active pairs returns [], not 404
# ---------------------------------------------------------------------------


def test_tc116_empty_active_pairs_returns_empty_list(db_session):
    """TC-116: list_as_of with NO active (design, grade) pairs → returns []."""
    svc = DashboardService(db_session)
    result = svc.list_as_of(date(2026, 6, 15))
    assert result == []


# ---------------------------------------------------------------------------
# TC-121 — Edge: ledger rows AFTER as_of_date are excluded
# ---------------------------------------------------------------------------


def test_tc121_rows_after_asof_excluded_from_sums(db_session):
    """TC-121: rows with txn_date > as_of_date MUST NOT affect inward/outward/adjust/closing."""
    d = _seed_design(db_session, None, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # Rows within window
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 3), "inward", 40, 40)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 10), "sale", -10, 30)
    # Row AFTER as_of_date — must be excluded
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 20), "inward", 50, 80)
    db_session.flush()

    svc = DashboardService(db_session)
    rows = svc.list_as_of(date(2026, 6, 15))

    assert len(rows) == 1
    row = rows[0]
    assert row.opening == 0
    assert row.inward == 40
    assert row.outward == 10
    assert row.adjust == 0
    assert row.closing == 30


# ---------------------------------------------------------------------------
# TC-127 — Service derives month_first = as_of_date.replace(day=1)
# ---------------------------------------------------------------------------


def test_tc127_month_first_derived_correctly(db_session):
    """TC-127: month_first = as_of_date.replace(day=1) passed to agg repo.

    Verified by inserting a May row (sets opening=50 for June 1) and a June row
    (counted in inward). If month_first were wrong the sums would be off.
    """
    d = _seed_design(db_session, None, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # May row — should become opening for June
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 5, 31), "inward", 50, 50)
    # June row — counted in inward for June
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 10), "inward", 20, 70)
    db_session.flush()

    svc = DashboardService(db_session)
    rows = svc.list_as_of(date(2026, 6, 15))

    assert len(rows) == 1
    row = rows[0]
    # opening = closing_balance(2026-05-31) = 50
    assert row.opening == 50
    # inward only counts June 1..15 — the May row must NOT be in inward
    assert row.inward == 20
    assert row.outward == 0
    assert row.adjust == 0
    assert row.closing == 70


# ---------------------------------------------------------------------------
# TC-128 — Edge: tampered running_balance triggers AssertionError (invariant)
# ---------------------------------------------------------------------------


def test_tc128_tampered_running_balance_raises_assertion_error(db_session):
    """TC-128: tampered running_balance → service raises AssertionError (invariant check)."""
    d = _seed_design(db_session, None, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")
    _seed_map(db_session, d.design_id, g.grade_id)

    # Normal first row
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 5), "inward", 100, 100)
    # Tampered second row — running_balance=999 instead of 70
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 10), "sale", -30, 999)
    db_session.flush()

    svc = DashboardService(db_session)
    with pytest.raises(AssertionError) as exc_info:
        svc.list_as_of(date(2026, 6, 15))

    assert "invariant" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# TC-129 — Result ordered by design_name ASC, grade_code ASC
# ---------------------------------------------------------------------------


def test_tc129_result_ordered_by_design_name_then_grade_code(db_session):
    """TC-129: list_as_of returns rows sorted by (design_name ASC, grade_code ASC)."""
    # Seed designs
    d_11x7 = TradingDesignModel(design_name="11X7 Ridges", size="11X7", is_active=True)
    d_12x8 = TradingDesignModel(design_name="12X8 Ridges", size="12X8", is_active=True)
    d_16x10 = TradingDesignModel(design_name="16X10 Ridges", size="16X10", is_active=True)
    db_session.add_all([d_11x7, d_12x8, d_16x10])
    db_session.flush()

    # Seed grades
    g_ob = GradeModel(grade_code="OB", is_active=True)
    g_1 = GradeModel(grade_code="1", is_active=True)
    g_2 = GradeModel(grade_code="2", is_active=True)
    db_session.add_all([g_ob, g_1, g_2])
    db_session.flush()

    # Insert maps in reverse order to test that sorting is applied by service
    # TC-129 input: pairs inserted as (12X8, OB), (16X10, 1), (12X8, 1), (11X7, 2)
    _seed_map(db_session, d_12x8.design_id, g_ob.grade_id)
    _seed_map(db_session, d_16x10.design_id, g_1.grade_id)
    _seed_map(db_session, d_12x8.design_id, g_1.grade_id)
    _seed_map(db_session, d_11x7.design_id, g_2.grade_id)
    db_session.flush()

    svc = DashboardService(db_session)
    rows = svc.list_as_of(date(2026, 6, 15))

    assert len(rows) == 4
    # Expected order: 11X7/2, 12X8/1, 12X8/OB, 16X10/1
    assert rows[0].design_name == "11X7 Ridges" and rows[0].grade_code == "2"
    assert rows[1].design_name == "12X8 Ridges" and rows[1].grade_code == "1"
    assert rows[2].design_name == "12X8 Ridges" and rows[2].grade_code == "OB"
    assert rows[3].design_name == "16X10 Ridges" and rows[3].grade_code == "1"
