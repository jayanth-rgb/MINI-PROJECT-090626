"""ST-009 — Sales Report HTTP latency benchmark (F-011).

Seeds 6 dealers × 12 months × 50 sales/month × 3 lines/sale = 10,800
sales_line rows. Measures p95 latency of GET /api/v1/reports/sales (no
filters) over 15 timed calls (2 warmups first). Threshold: p95 < 2000ms
per ST-009 spec and PRD non_functional.performance.
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

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
# Seed helpers (inlined — not imported)
# ---------------------------------------------------------------------------

def _seed_staff(db):
    """Seed loader + verifier staff (required FKs on SalesHeaderModel)."""
    loader = StaffModel(staff_name="ST009 Loader")
    verifier = StaffModel(staff_name="ST009 Verifier")
    db.add_all([loader, verifier])
    db.flush()
    return loader.staff_id, verifier.staff_id


def _seed_dealer(db, name: str, place: str) -> DealerModel:
    d = DealerModel(dealer_name=name, place=place, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_sale(db, sales_date, dealer_id, place_snapshot, loader_id, verifier_id, lines):
    """lines: list of dicts {design_id, grade_id, nos}"""
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


def test_st009(client, db_session):
    """ST-009: Sales Report HTTP p95 < 2000ms with ~10,800 sales_line rows."""
    # ------------------------------------------------------------------
    # Seed masters: 6 dealers, 3 designs, 3 grades
    # ------------------------------------------------------------------
    loader_id, verifier_id = _seed_staff(db_session)

    dealers = []
    for i in range(6):
        d = _seed_dealer(db_session, f"ST009 Dealer {i + 1}", f"ST9City{i + 1}")
        dealers.append(d)

    designs = []
    for name, size in [
        ("ST009 16X10 Ridges", "16X10"),
        ("ST009 12X8 Ridges", "12X8"),
        ("ST009 11X7 Ridges", "11X7"),
    ]:
        td = TradingDesignModel(design_name=name, size=size, is_active=True)
        db_session.add(td)
        designs.append(td)
    db_session.flush()

    grades = []
    for code in ["ST9-1", "ST9-2", "ST9-OB"]:
        g = GradeModel(grade_code=code, is_active=True)
        db_session.add(g)
        grades.append(g)
    db_session.flush()

    # 3 line templates (one per design+grade combo)
    line_combos = [
        {"design_id": designs[0].design_id, "grade_id": grades[0].grade_id, "nos": 5},
        {"design_id": designs[1].design_id, "grade_id": grades[1].grade_id, "nos": 10},
        {"design_id": designs[2].design_id, "grade_id": grades[2].grade_id, "nos": 15},
    ]

    # ------------------------------------------------------------------
    # Seed 6 dealers × 12 months × 50 sales/month = 3600 headers
    #   × 3 lines/sale = 10,800 sales_line rows.
    # Months: July 2025 through June 2026.
    # Days spread across [1..28] via modulo to avoid month-end boundary issues.
    # ------------------------------------------------------------------
    base_year, base_month_num = 2025, 7
    total_headers = 0

    for month_offset in range(12):
        raw_month = base_month_num + month_offset - 1  # 0-indexed
        year = base_year + raw_month // 12
        month = raw_month % 12 + 1

        for dealer in dealers:
            for sale_idx in range(50):
                day = (sale_idx % 28) + 1
                sale_date = date(year, month, day)
                _seed_sale(
                    db_session,
                    sale_date,
                    dealer.dealer_id,
                    dealer.place,
                    loader_id,
                    verifier_id,
                    line_combos,
                )
                total_headers += 1

        # Flush per month to avoid excessive memory accumulation
        db_session.flush()

    total_lines = total_headers * 3  # 3 lines per header

    # ------------------------------------------------------------------
    # 2 warmup calls
    # ------------------------------------------------------------------
    for _ in range(2):
        resp = client.get("/api/v1/reports/sales")
        assert resp.status_code == 200, f"Warmup call failed: {resp.status_code} {resp.text}"

    # ------------------------------------------------------------------
    # 15 timed calls (no filters)
    # ------------------------------------------------------------------
    SAMPLES = 15
    durations_ms: list[float] = []
    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/reports/sales")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(elapsed_ms)
        assert resp.status_code == 200, f"Timed call failed: {resp.status_code} {resp.text}"

    durations_ms.sort()
    p50 = statistics.median(durations_ms)
    p95_idx = int(SAMPLES * 0.95)
    p95 = durations_ms[p95_idx]

    print(
        f"\n[ST-009] Sales Report HTTP latency (ms): "
        f"p50={p50:.1f} p95={p95:.1f} "
        f"headers_seeded={total_headers} lines_seeded={total_lines} "
        f"samples={SAMPLES} threshold_ms_p95=2000"
    )

    assert p95 < 2000.0, (
        f"ST-009 FAIL: p95={p95:.1f}ms exceeds 2000ms budget "
        f"(p50={p50:.1f}, headers={total_headers}, lines={total_lines})"
    )
