"""TC-123, TC-124, TC-125, TC-126 — LedgerAggregatesRepository.sum_deltas_by_source_type.

These run against the testcontainers PG (db_session fixture) because they require
a real SQL GROUP BY with CASE-conditional SUMs per DS-016. Edge cases are
co-located here per project convention.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel
from src.infrastructure.db.repositories.ledger_aggregates import LedgerAggregatesRepository


# ---------------------------------------------------------------------------
# In-file seed helpers
# ---------------------------------------------------------------------------


def _seed_design(db, name="Test Design", size="16X10"):
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, code="1"):
    g = GradeModel(grade_code=code, is_active=True)
    db.add(g)
    db.flush()
    return g


def _seed_ledger(db, design_id, grade_id, txn_date, source_type, delta, running_balance=0):
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
# TC-123 — Basic multi-source GROUP BY returns correct sums
# ---------------------------------------------------------------------------


def test_tc123_sum_deltas_returns_correct_aggregates_per_pair(db_session):
    """TC-123: inward_sum/outward_sum/adjust_sum correctly grouped by (design, grade).

    outward_sum reads positive (negated delta for 'sale' rows per DS-016).
    Two separate (design, grade) pairs should produce two independent rows.
    """
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")

    # Pair (d, g1): inward=40, sale=-25, adjustment=+10
    _seed_ledger(db_session, d.design_id, g1.grade_id, date(2026, 6, 3), "inward", 40, 40)
    _seed_ledger(db_session, d.design_id, g1.grade_id, date(2026, 6, 10), "sale", -25, 15)
    _seed_ledger(db_session, d.design_id, g1.grade_id, date(2026, 6, 12), "adjustment", 10, 25)

    # Pair (d, g2): inward=15 only
    _seed_ledger(db_session, d.design_id, g2.grade_id, date(2026, 6, 8), "inward", 15, 15)
    db_session.flush()

    repo = LedgerAggregatesRepository(db_session)
    rows = repo.sum_deltas_by_source_type(date(2026, 6, 1), date(2026, 6, 15))

    assert len(rows) == 2
    by_key = {(r.design_id, r.grade_id): r for r in rows}

    r1 = by_key[(d.design_id, g1.grade_id)]
    assert int(r1.inward_sum) == 40
    assert int(r1.outward_sum) == 25   # -(-25) = +25
    assert int(r1.adjust_sum) == 10

    r2 = by_key[(d.design_id, g2.grade_id)]
    assert int(r2.inward_sum) == 15
    assert int(r2.outward_sum) == 0
    assert int(r2.adjust_sum) == 0


# ---------------------------------------------------------------------------
# TC-124 — Edge: empty date window returns empty list
# ---------------------------------------------------------------------------


def test_tc124_empty_date_window_returns_empty_list(db_session):
    """TC-124: no rows in the queried range → returns []."""
    repo = LedgerAggregatesRepository(db_session)
    rows = repo.sum_deltas_by_source_type(date(2026, 1, 1), date(2026, 1, 31))
    assert rows == []


# ---------------------------------------------------------------------------
# TC-125 — Edge: outward_sum reads positive (negated from negative delta)
# ---------------------------------------------------------------------------


def test_tc125_outward_sum_reads_positive_from_negative_sale_deltas(db_session):
    """TC-125: CASE WHEN source_type='sale' THEN -delta → outward_sum is positive."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")

    # Two sale rows with negative deltas
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 5), "sale", -15, -15)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 15), "sale", -25, -40)
    db_session.flush()

    repo = LedgerAggregatesRepository(db_session)
    rows = repo.sum_deltas_by_source_type(date(2026, 6, 1), date(2026, 6, 30))

    assert len(rows) == 1
    r = rows[0]
    assert int(r.inward_sum) == 0
    assert int(r.outward_sum) == 40   # -(-15) + -(-25) = 15 + 25 = 40
    assert int(r.adjust_sum) == 0


# ---------------------------------------------------------------------------
# TC-126 — Edge: adjust_sum preserves signed values (can be negative)
# ---------------------------------------------------------------------------


def test_tc126_adjust_sum_preserves_signed_values(db_session):
    """TC-126: adjust_sum = SUM(delta for adjustments) — can be negative."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g = _seed_grade(db_session, "1")

    # Positive adjustment +5, negative adjustment -12 → net = -7
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 10), "adjustment", 5, 5)
    _seed_ledger(db_session, d.design_id, g.grade_id, date(2026, 6, 20), "adjustment", -12, -7)
    db_session.flush()

    repo = LedgerAggregatesRepository(db_session)
    rows = repo.sum_deltas_by_source_type(date(2026, 6, 1), date(2026, 6, 30))

    assert len(rows) == 1
    r = rows[0]
    assert int(r.inward_sum) == 0
    assert int(r.outward_sum) == 0
    assert int(r.adjust_sum) == -7
