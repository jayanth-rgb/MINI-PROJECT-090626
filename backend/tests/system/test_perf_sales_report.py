"""TC-157 — SalesReportService unfiltered query performance benchmark.

Manual benchmark using time.perf_counter() (no pytest-benchmark required).
Seed: ~12 months × ~80 sales/month × ~3 lines/sale ≈ 2880 sales_line rows.
Threshold: p95 < 2000ms (PRD non_functional.performance: Sales Report < 2s for
1 year of data unfiltered).
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

import pytest

from src.application.services.sales_report_service import SalesReportService
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

def _seed_perf_data(db_session) -> None:
    """Seed ~12 months × ~80 sales/month × ~3 lines/sale for TC-157.

    Uses 6 dealers, 3 designs, 3 grades — deterministic, no random().
    Total: 12 months × 80 headers × 3 lines = 2880 sales_line rows (approx).
    """
    # Staff
    loader = StaffModel(staff_name="Perf Loader")
    verifier = StaffModel(staff_name="Perf Verifier")
    db_session.add_all([loader, verifier])
    db_session.flush()

    # 6 dealers
    dealers = []
    for i in range(6):
        d = DealerModel(
            dealer_name=f"Perf Dealer {i + 1}",
            place=f"City{i + 1}",
            is_active=True,
        )
        db_session.add(d)
        dealers.append(d)
    db_session.flush()

    # 3 designs × 3 grades
    designs = []
    for i, (name, size) in enumerate([
        ("16X10 Ridges", "16X10"),
        ("12X8 Ridges", "12X8"),
        ("11X7 Ridges", "11X7"),
    ]):
        d = TradingDesignModel(design_name=name, size=size, is_active=True)
        db_session.add(d)
        designs.append(d)
    db_session.flush()

    grades = []
    for code in ["1", "2", "OB"]:
        g = GradeModel(grade_code=code, is_active=True)
        db_session.add(g)
        grades.append(g)
    db_session.flush()

    # Seed 12 months of data (July 2025 through June 2026)
    # ~80 sales per month, spread across 6 dealers.
    # 80 / 6 ≈ 13.3 headers per dealer per month → use 14 for first 2, 13 for rest.
    # 14×2 + 13×4 = 28 + 52 = 80 headers/month × 12 months = 960 headers total.
    # Each header: 3 lines → 2880 sales_line rows.
    header_count = 0
    for month_offset in range(12):
        # Months: 2025-07 to 2026-06
        year = 2025 + (month_offset + 6) // 12
        month = ((month_offset + 6) % 12) + 1
        headers_per_dealer = [14, 14, 13, 13, 13, 13]  # 80 total

        for dealer_idx, (dealer, hdrs) in enumerate(zip(dealers, headers_per_dealer)):
            for h in range(hdrs):
                # Spread evenly across the month: day = (h % 28) + 1
                day = (h % 28) + 1
                try:
                    sale_date = date(year, month, day)
                except ValueError:
                    sale_date = date(year, month, 28)

                header = SalesHeaderModel(
                    sales_date=sale_date,
                    dealer_id=dealer.dealer_id,
                    place=dealer.place,
                    loading_staff_id=loader.staff_id,
                    verified_by_id=verifier.staff_id,
                )
                db_session.add(header)
                header_count += 1

                # Flush every 200 headers to avoid excessive memory usage
                if header_count % 200 == 0:
                    db_session.flush()

        db_session.flush()

        # Now add lines for the headers added in this month-dealer batch.
        # We query the headers without lines yet.

    # Flush all headers first
    db_session.flush()

    # Add 3 lines per header (round-robin across design×grade combos)
    headers = db_session.query(SalesHeaderModel).all()
    line_combos = [
        (designs[0], grades[0]),
        (designs[1], grades[1]),
        (designs[2], grades[2]),
    ]
    for header in headers:
        for combo_idx, (design, grade) in enumerate(line_combos):
            sl = SalesLineModel(
                header_id=header.header_id,
                design_id=design.design_id,
                grade_id=grade.grade_id,
                nos=(combo_idx + 1) * 5,  # 5, 10, 15 — deterministic
            )
            db_session.add(sl)

    db_session.flush()


# ---------------------------------------------------------------------------
# TC-157: p95 latency < 2000ms over 10 calls
# ---------------------------------------------------------------------------

def test_tc157_sales_report_p95_latency(db_session):
    """Performance: Sales Report unfiltered p95 < 2000ms with ~2880 sales_line rows.

    10 iterations of SalesReportService.generate(no filters); threshold per
    PRD non_functional.performance and TC-157 spec.
    """
    _seed_perf_data(db_session)

    svc = SalesReportService(db_session)

    # Warm-up: 2 calls to amortise first-time connection/query plan overhead
    for _ in range(2):
        svc.generate()

    # Measure: 10 sequential generate() calls
    iterations = 10
    durations_ms: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        svc.generate()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(elapsed_ms)

    # Compute p95 using statistics.quantiles (at least 10 data points required)
    quantiles = statistics.quantiles(durations_ms, n=100)
    p50 = quantiles[49]   # 50th percentile
    p95 = quantiles[94]   # 95th percentile

    print(
        f"\n[TC-157] SalesReport generate() latency (ms): "
        f"p50={p50:.1f} p95={p95:.1f} "
        f"(threshold=2000ms, iterations={iterations})"
    )

    assert p95 < 2000.0, (
        f"TC-157 FAIL: p95={p95:.1f}ms exceeds 2000ms budget "
        f"(p50={p50:.1f}, threshold=2000ms)"
    )
