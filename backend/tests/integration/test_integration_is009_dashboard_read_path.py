"""IS-009 — DF-004 happy path: seeded ledger → GET /dashboard returns correct
opening/inward/outward/adjust/closing per (design, grade) with sort + invariant.

Exercises the READ path in isolation: ledger rows seeded directly via
StockLedgerModel inserts (bypasses domain.stock). DashboardService.list_as_of
composes list_active_all + sum_deltas_by_source_type + domain.stock
opening/closing balance calls against the real testcontainers PG.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def test_is009(client, db_session):
    # ------------------------------------------------------------------ seed master
    # D1 = 12X8 Ridges (zero-history pair), D2 = 16X10 Ridges (has ledger)
    d1 = TradingDesignModel(design_name="12X8 Ridges", size="12X8", is_active=True)
    d2 = TradingDesignModel(design_name="16X10 Ridges", size="16X10", is_active=True)
    g1 = GradeModel(grade_code="1", is_active=True)
    g2 = GradeModel(grade_code="2", is_active=True)
    db_session.add_all([d1, d2, g1, g2])
    db_session.flush()

    # Active pairs: (12X8+G1), (16X10+G1), (16X10+G2)
    db_session.add_all([
        DesignGradeMapModel(design_id=d1.design_id, grade_id=g1.grade_id, is_active=True),
        DesignGradeMapModel(design_id=d2.design_id, grade_id=g1.grade_id, is_active=True),
        DesignGradeMapModel(design_id=d2.design_id, grade_id=g2.grade_id, is_active=True),
    ])
    db_session.flush()

    # ------------------------------------------------------------------ seed ledger
    # (16X10 Ridges, G1) — May 31 inward delta=+50 running=50
    #                       June 5 inward delta=+30 running=80
    #                       June 20 sale delta=-12 running=68
    # opening(June 1) = closing_balance(May 31) = 50
    # June inward = 30, June outward = 12, June adjust = 0, closing = 68
    db_session.add_all([
        StockLedgerModel(
            design_id=d2.design_id, grade_id=g1.grade_id,
            txn_date=date(2026, 5, 31), source_type="inward",
            delta=50, running_balance=50,
            source_header_id=1, source_line_id=1,
        ),
        StockLedgerModel(
            design_id=d2.design_id, grade_id=g1.grade_id,
            txn_date=date(2026, 6, 5), source_type="inward",
            delta=30, running_balance=80,
            source_header_id=2, source_line_id=2,
        ),
        StockLedgerModel(
            design_id=d2.design_id, grade_id=g1.grade_id,
            txn_date=date(2026, 6, 20), source_type="sale",
            delta=-12, running_balance=68,
            source_header_id=3, source_line_id=3,
        ),
    ])
    # (16X10 Ridges, G2) — May 28 inward delta=+40 running=40
    #                       June 10 adjustment delta=+5 running=45
    # opening(June 1) = closing_balance(May 31) = 40
    # June inward = 0, June outward = 0, June adjust = 5, closing = 45
    db_session.add_all([
        StockLedgerModel(
            design_id=d2.design_id, grade_id=g2.grade_id,
            txn_date=date(2026, 5, 28), source_type="inward",
            delta=40, running_balance=40,
            source_header_id=4, source_line_id=4,
        ),
        StockLedgerModel(
            design_id=d2.design_id, grade_id=g2.grade_id,
            txn_date=date(2026, 6, 10), source_type="adjustment",
            delta=5, running_balance=45,
            source_header_id=5, source_line_id=5,
        ),
    ])
    # (12X8 Ridges, G1) — no ledger rows (zero-history pair)
    db_session.flush()

    # ------------------------------------------------------------------ call
    resp = client.get("/api/v1/dashboard?as_of_date=2026-06-30")
    assert resp.status_code == 200, resp.text

    body = resp.json()

    # Exactly 3 rows
    assert len(body) == 3, f"Expected 3 rows, got {len(body)}: {body}"

    # All 10 fields present per row
    required_keys = {
        "design_id", "design_name", "size",
        "grade_id", "grade_code",
        "opening", "inward", "outward", "adjust", "closing",
    }
    for row in body:
        assert required_keys.issubset(row.keys()), f"Missing fields in row: {row}"

    # Sort order: design_name ASC, grade_code ASC
    # Expected: 12X8 Ridges/1, 16X10 Ridges/1, 16X10 Ridges/2
    expected_rows = [
        {"design_name": "12X8 Ridges",  "grade_code": "1", "opening": 0,  "inward": 0,  "outward": 0,  "adjust": 0, "closing": 0},
        {"design_name": "16X10 Ridges", "grade_code": "1", "opening": 50, "inward": 30, "outward": 12, "adjust": 0, "closing": 68},
        {"design_name": "16X10 Ridges", "grade_code": "2", "opening": 40, "inward": 0,  "outward": 0,  "adjust": 5, "closing": 45},
    ]

    for i, (row, exp) in enumerate(zip(body, expected_rows)):
        assert row["design_name"] == exp["design_name"], (
            f"Row {i}: design_name expected={exp['design_name']!r}, got={row['design_name']!r}"
        )
        assert row["grade_code"] == exp["grade_code"], (
            f"Row {i}: grade_code expected={exp['grade_code']!r}, got={row['grade_code']!r}"
        )
        assert row["opening"] == exp["opening"], (
            f"Row {i} ({row['design_name']}/{row['grade_code']}): opening expected={exp['opening']}, got={row['opening']}"
        )
        assert row["inward"] == exp["inward"], (
            f"Row {i} ({row['design_name']}/{row['grade_code']}): inward expected={exp['inward']}, got={row['inward']}"
        )
        assert row["outward"] == exp["outward"], (
            f"Row {i} ({row['design_name']}/{row['grade_code']}): outward expected={exp['outward']}, got={row['outward']}"
        )
        assert row["adjust"] == exp["adjust"], (
            f"Row {i} ({row['design_name']}/{row['grade_code']}): adjust expected={exp['adjust']}, got={row['adjust']}"
        )
        assert row["closing"] == exp["closing"], (
            f"Row {i} ({row['design_name']}/{row['grade_code']}): closing expected={exp['closing']}, got={row['closing']}"
        )

    # FORMULA-001 client-side verification: opening + inward - outward + adjust == closing
    for row in body:
        invariant = row["opening"] + row["inward"] - row["outward"] + row["adjust"]
        assert invariant == row["closing"], (
            f"FORMULA-001 violated for {row['design_name']}/{row['grade_code']}: "
            f"{row['opening']} + {row['inward']} - {row['outward']} + {row['adjust']} "
            f"= {invariant} != {row['closing']}"
        )
