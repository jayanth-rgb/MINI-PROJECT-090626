"""TC-122 — Dashboard p95 latency benchmark (F-010, AC-045).

Seeds 6 active pairs × 12 months × 28 txns/month = 2016 ledger rows total
(one txn per unique day-of-month per pair so date+ledger_id ordering is
unambiguous, and running_balance is cumulative across months per pair —
required for the FORMULA-001 invariant the service asserts per row).
Measures p95 latency of DashboardService.list_as_of over 20 calls.
Threshold: p95 < 500ms per DS-016 + PRD non_functional.performance.
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

from src.application.services.dashboard_service import DashboardService
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


# ---------------------------------------------------------------------------
# TC-122 — p95 < 500ms with 12 months of accumulated ledger rows
# ---------------------------------------------------------------------------


def test_tc122_dashboard_p95_under_500ms(db_session):
    """TC-122: Dashboard with ~4320 ledger rows must have p95 < 500ms (DS-016 + AC-045)."""
    # Seed 6 active (design, grade) pairs
    designs = []
    for i in range(3):
        d = TradingDesignModel(
            design_name=f"Design {i + 1}",
            size=f"{16 - i * 2}X{10 - i * 2}",
            is_active=True,
        )
        db_session.add(d)
        designs.append(d)
    db_session.flush()

    grades = []
    for code in ["1", "2"]:
        g = GradeModel(grade_code=code, is_active=True)
        db_session.add(g)
        grades.append(g)
    db_session.flush()

    pairs = []
    for d in designs:
        for g in grades:
            m = DesignGradeMapModel(design_id=d.design_id, grade_id=g.grade_id, is_active=True)
            db_session.add(m)
            pairs.append((d.design_id, g.grade_id))
    db_session.flush()

    # Seed 12 months × 28 txns/month per pair = 336 rows/pair × 6 pairs = 2016 rows.
    # One txn per unique day-of-month so (txn_date DESC, ledger_id DESC) tie-break is
    # unambiguous and the FORMULA-001 invariant (opening + inward - outward + adjust
    # == closing) holds at every (design, grade) read by the dashboard.
    # Months: July 2025 through June 2026.
    base_month = date(2025, 7, 1)
    # Cumulative running_balance per (design, grade) — persists across months so
    # opening_balance(month_first) == closing_balance(month_first - 1 day) by construction.
    balance_by_pair: dict[tuple[int, int], int] = {pair: 500 for pair in pairs}
    row_counter = 0
    for month_offset in range(12):
        month_start = date(
            base_month.year + (base_month.month + month_offset - 1) // 12,
            (base_month.month + month_offset - 1) % 12 + 1,
            1,
        )
        for design_id, grade_id in pairs:
            key = (design_id, grade_id)
            for day_offset in range(28):
                txn_date = month_start + timedelta(days=day_offset)
                # Repeating 3-cycle mix: per 3 days net delta = +2 - 1 + 1 = +2.
                if day_offset % 3 == 0:
                    source_type, delta = "inward", 2
                elif day_offset % 3 == 1:
                    source_type, delta = "sale", -1
                else:
                    source_type, delta = "adjustment", 1
                balance_by_pair[key] += delta
                row = StockLedgerModel(
                    design_id=design_id,
                    grade_id=grade_id,
                    txn_date=txn_date,
                    source_type=source_type,
                    delta=delta,
                    running_balance=balance_by_pair[key],
                    source_header_id=row_counter + 1,
                    source_line_id=1,
                )
                db_session.add(row)
                row_counter += 1

    db_session.flush()

    svc = DashboardService(db_session)
    as_of = date(2026, 6, 15)

    # Warm-up: 2 calls before measuring
    svc.list_as_of(as_of)
    svc.list_as_of(as_of)

    # Measure: 20 sequential calls
    durations_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        result = svc.list_as_of(as_of)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(elapsed_ms)

    durations_ms.sort()
    p95_idx = int(len(durations_ms) * 0.95)
    p95 = durations_ms[p95_idx]
    p50 = statistics.median(durations_ms)
    print(
        f"\n[TC-122] Dashboard latency (ms): "
        f"p50={p50:.1f} p95={p95:.1f} rows_seeded={row_counter} result_rows={len(result)}"
    )

    assert p95 < 500.0, (
        f"TC-122 FAIL: p95={p95:.1f}ms exceeds 500ms budget "
        f"(p50={p50:.1f}, rows_seeded={row_counter})"
    )
