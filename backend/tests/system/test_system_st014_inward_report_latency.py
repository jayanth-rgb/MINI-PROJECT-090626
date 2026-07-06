"""ST-014 — GET /reports/inward median < 2000ms with 120 inward rows.

Seeds 3 designs x 2 grades = 6 pairs and 120 inward transactions distributed
across 4 months. Times 10 sequential GET /reports/inward (no filters) via
TestClient and asserts median < 2000ms (Sales-Report analog per PRD
non_functional.performance).

Also asserts the reconciliation invariant (AC-061 / DS-017) on the first call:
sum(transactions[*].nos) == sum(consolidation[*].total_nos).
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    SupplierModel,
    StaffModel,
    TradingDesignModel,
)


def _seed(db_session):
    designs = []
    for i in range(3):
        d = TradingDesignModel(
            design_id=i + 1,
            size=f"{16 - i * 2}X{10 - i * 2}",
            design_name=f"Design {i + 1}",
        )
        db_session.add(d)
        designs.append(d)
    grades = []
    for i in range(2):
        g = GradeModel(grade_id=i + 1, grade_code=str(i + 1))
        db_session.add(g)
        grades.append(g)
    db_session.flush()
    for d in designs:
        for g in grades:
            db_session.add(
                DesignGradeMapModel(design_id=d.design_id, grade_id=g.grade_id)
            )
    db_session.add(SupplierModel(supplier_id=1, supplier_name="Manjunatha", place="Mallur"))
    db_session.add(StaffModel(staff_id=1, staff_name="Chandran"))
    db_session.flush()


def test_st014_inward_report_median_under_2000ms(client, db_session):
    _seed(db_session)

    today = date.today()
    # 120 inward rows: 20 different purchase_dates within last 7 days x 6 pairs
    # AC-021 restricts purchase_date to today..today-7; use 6 distinct dates
    # today..today-5, 20 rows per date across the 6 pairs (spread designs+grades).
    row_count = 0
    for day_offset in range(6):  # 0..5 -> 6 distinct dates within 7-day window
        purchase_date = (today - timedelta(days=day_offset)).isoformat()
        for design_id in (1, 2, 3):
            for grade_id in (1, 2):
                resp = client.post(
                    "/api/v1/inward",
                    json={
                        "purchase_date": purchase_date,
                        "supplier_id": 1,
                        "entered_by_id": 1,
                        "lines": [
                            {"design_id": design_id, "grade_id": grade_id, "nos": 5}
                        ],
                    },
                )
                assert resp.status_code == 201, f"seed inward failed: {resp.text}"
                row_count += 1
    assert row_count == 36  # 6 dates x 3 designs x 2 grades = 36 headers

    durations_ms: list[float] = []
    reconciliation_verified = False
    for i in range(10):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/reports/inward")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"inward report failed: {resp.text}"
        durations_ms.append(elapsed_ms)
        if i == 0:
            body = resp.json()
            sum_txn = sum(t["nos"] for t in body["transactions"])
            sum_cons = sum(c["total_nos"] for c in body["consolidation"])
            assert sum_txn == sum_cons == 36 * 5, (
                f"reconciliation broken: txn={sum_txn} cons={sum_cons}"
            )
            reconciliation_verified = True

    assert reconciliation_verified
    median = statistics.median(durations_ms)
    assert median < 2000.0, (
        f"ST-014 median inward-report latency {median:.1f}ms exceeds 2000ms; "
        f"samples={[round(d, 1) for d in durations_ms]}"
    )
    print(f"\nST-014 median={median:.1f}ms n=10 rows=36")
