"""ST-008 — Dashboard HTTP latency benchmark (AC-045, F-010).

Seeds 6 active design-grade pairs × 12 months × 28 txns/month = 2016 ledger
rows with cumulative running_balance per pair (FORMULA-001 invariant satisfied).
Measures p95 latency of GET /api/v1/dashboard?as_of_date=<today> over 30 timed
calls (3 warmups first). Threshold: p95 < 800ms per ST-008 spec.

Distinct from TC-122 which measured service-layer only — this measures the
full HTTP stack: TestClient → router → DI → service → repo → testcontainers PG.
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def test_st008(client, db_session):
    """ST-008: Dashboard HTTP p95 < 800ms with 2016 ledger rows (6 pairs × 12 months × 28 txns)."""
    # ------------------------------------------------------------------
    # Seed 6 active (design, grade) pairs — 3 designs × 2 grades each
    # ------------------------------------------------------------------
    designs = []
    for i in range(3):
        d = TradingDesignModel(
            design_name=f"ST008 Design {i + 1}",
            size=f"{16 - i * 2}X{10 - i * 2}",
            is_active=True,
        )
        db_session.add(d)
        designs.append(d)
    db_session.flush()

    grades = []
    for code in ["1", "2"]:
        g = GradeModel(grade_code=f"ST8-{code}", is_active=True)
        db_session.add(g)
        grades.append(g)
    db_session.flush()

    pairs = []
    for d in designs:
        for g in grades:
            m = DesignGradeMapModel(
                design_id=d.design_id, grade_id=g.grade_id, is_active=True
            )
            db_session.add(m)
            pairs.append((d.design_id, g.grade_id))
    db_session.flush()

    # ------------------------------------------------------------------
    # Seed 12 months × 28 txns/month per pair = 336 rows/pair × 6 = 2016 rows.
    # Months: July 2025 through June 2026.
    # Cumulative running_balance per pair across months — FORMULA-001 holds.
    # Day offset in [0..27] → unique date per txn within a month.
    # ------------------------------------------------------------------
    base_year, base_month = 2025, 7
    # running_balance starts at 500 per pair and accumulates net delta across
    # all months (same pattern as test_perf_dashboard.py canonical reference).
    balance_by_pair: dict[tuple[int, int], int] = {pair: 500 for pair in pairs}
    row_counter = 0

    for month_offset in range(12):
        raw_month = base_month + month_offset - 1  # 0-indexed
        year = base_year + raw_month // 12
        month = raw_month % 12 + 1
        month_start = date(year, month, 1)

        for design_id, grade_id in pairs:
            key = (design_id, grade_id)
            for day_offset in range(28):
                txn_date = month_start + timedelta(days=day_offset)
                # 3-cycle mix: +2 / -1 / +1 per 3 days (net +2 per cycle)
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
    as_of = date.today().isoformat()

    # ------------------------------------------------------------------
    # 3 warmup calls — amortise connection setup and query plan caching
    # ------------------------------------------------------------------
    for _ in range(3):
        resp = client.get(f"/api/v1/dashboard?as_of_date={as_of}")
        assert resp.status_code == 200, f"Warmup call failed: {resp.status_code} {resp.text}"

    # ------------------------------------------------------------------
    # 30 timed calls
    # ------------------------------------------------------------------
    SAMPLES = 30
    durations_ms: list[float] = []
    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        resp = client.get(f"/api/v1/dashboard?as_of_date={as_of}")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(elapsed_ms)
        assert resp.status_code == 200, f"Timed call failed: {resp.status_code} {resp.text}"

    durations_ms.sort()
    p50 = statistics.median(durations_ms)
    p95_idx = int(SAMPLES * 0.95)
    p95 = durations_ms[p95_idx]

    print(
        f"\n[ST-008] Dashboard HTTP latency (ms): "
        f"p50={p50:.1f} p95={p95:.1f} "
        f"rows_seeded={row_counter} samples={SAMPLES} "
        f"threshold_ms_p95=800"
    )

    assert p95 < 800.0, (
        f"ST-008 FAIL: p95={p95:.1f}ms exceeds 800ms budget "
        f"(p50={p50:.1f}, rows_seeded={row_counter})"
    )
