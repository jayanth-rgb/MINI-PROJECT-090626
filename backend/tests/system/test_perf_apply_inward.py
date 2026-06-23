"""ST-004 — apply_inward latency benchmark.

Manual benchmark using time.perf_counter() since pytest-benchmark isn't
guaranteed installed. Threshold: p95 < 100ms per call on testcontainers PG.
"""
from __future__ import annotations

import time
from datetime import date

from src.domain import stock
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def test_st004_apply_inward_p95_latency(db_session):
    """50 samples of apply_inward; p95 must be < 100ms (S2 write-path budget)."""
    design = TradingDesignModel(size="16X10", design_name="Perf design")
    grade = GradeModel(grade_code="P")
    db_session.add_all([design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    db_session.commit()

    # Warm-up: 3 calls to amortize first-time JIT / connection warmup
    for i in range(3):
        stock.apply_inward(
            db_session, design.design_id, grade.grade_id, date(2026, 6, 1), 1, i, 1
        )
    db_session.commit()

    # Measure: 50 sequential inward calls; commit per call (realistic write path)
    durations_ms: list[float] = []
    for i in range(50):
        t0 = time.perf_counter()
        stock.apply_inward(
            db_session,
            design.design_id,
            grade.grade_id,
            date(2026, 6, 1),
            1,
            100 + i,
            1,
        )
        db_session.commit()
        durations_ms.append((time.perf_counter() - t0) * 1000.0)

    durations_ms.sort()
    p50 = durations_ms[len(durations_ms) // 2]
    p95 = durations_ms[int(len(durations_ms) * 0.95)]
    p99 = durations_ms[int(len(durations_ms) * 0.99)]
    print(f"\n[ST-004] apply_inward latency (ms): p50={p50:.1f} p95={p95:.1f} p99={p99:.1f}")
    assert p95 < 100.0, (
        f"ST-004 FAIL: p95={p95:.1f}ms exceeds 100ms budget "
        f"(p50={p50:.1f}, p99={p99:.1f})"
    )
