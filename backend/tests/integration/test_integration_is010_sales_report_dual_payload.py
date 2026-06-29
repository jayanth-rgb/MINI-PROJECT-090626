"""IS-010 — DF-005 happy path: seeded sales → GET /reports/sales with 3 of 5
filters returns reconciled dual-payload.

Filters: date_from=2026-06-01, date_to=2026-06-30, dealer_ids=[dealer1], places=Mysuru
4 sales seeded; Bengaluru sale (place filter) and July sale (date filter) excluded.
Expected: transactions=4 lines, consolidation=3 groups, reconciliation sum=28.
AC-050: sum(transactions.nos) == sum(consolidation.total_nos) == 28.
"""
from __future__ import annotations

from datetime import date

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
# Inline seed helpers (self-contained — NOT added to conftest)
# ---------------------------------------------------------------------------

def _seed_staff(db):
    """Seed loader + verifier staff (required FKs on SalesHeaderModel)."""
    loader = StaffModel(staff_name="Loader A")
    verifier = StaffModel(staff_name="Verifier B")
    db.add_all([loader, verifier])
    db.flush()
    return loader.staff_id, verifier.staff_id


def _seed_dealer(db, name: str, place: str) -> DealerModel:
    d = DealerModel(dealer_name=name, place=place, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_design(db, name: str, size: str) -> TradingDesignModel:
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, code: str) -> GradeModel:
    g = GradeModel(grade_code=code, is_active=True)
    db.add(g)
    db.flush()
    return g


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


def test_is010(client, db_session):
    # ------------------------------------------------------------------ seed master
    loader_id, verifier_id = _seed_staff(db_session)
    # IS-010 scenario: 2 dealers
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Mysuru")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Bengaluru")
    # 2 designs: D1=16X10 Ridges, D2=12X8 Ridges
    d1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    d2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    # 2 grades: G1 and G2
    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")

    # ------------------------------------------------------------------ seed 4 sales
    # Sale 1: 2026-06-05, dealer=Raj, place=Mysuru, lines=[D1/G1=10, D2/G2=4]
    # → IN window, IN places filter → 2 lines included
    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Mysuru",
        loader_id, verifier_id,
        [
            {"design_id": d1.design_id, "grade_id": g1.grade_id, "nos": 10},
            {"design_id": d2.design_id, "grade_id": g2.grade_id, "nos": 4},
        ],
    )

    # Sale 2: 2026-06-15, dealer=Raj, place=Mysuru, lines=[D1/G1=6, D1/G2=8]
    # → IN window, IN places filter → 2 lines included
    _seed_sale(
        db_session, date(2026, 6, 15), dealer1.dealer_id, "Mysuru",
        loader_id, verifier_id,
        [
            {"design_id": d1.design_id, "grade_id": g1.grade_id, "nos": 6},
            {"design_id": d1.design_id, "grade_id": g2.grade_id, "nos": 8},
        ],
    )

    # Sale 3: 2026-06-20, dealer=Sri, place=Bengaluru → EXCLUDED by places filter
    _seed_sale(
        db_session, date(2026, 6, 20), dealer2.dealer_id, "Bengaluru",
        loader_id, verifier_id,
        [
            {"design_id": d1.design_id, "grade_id": g1.grade_id, "nos": 9},
            {"design_id": d2.design_id, "grade_id": g1.grade_id, "nos": 3},
        ],
    )

    # Sale 4: 2026-07-02, dealer=Raj, place=Mysuru → EXCLUDED by date_to=2026-06-30
    _seed_sale(
        db_session, date(2026, 7, 2), dealer1.dealer_id, "Mysuru",
        loader_id, verifier_id,
        [{"design_id": d1.design_id, "grade_id": g1.grade_id, "nos": 5}],
    )

    # ------------------------------------------------------------------ call
    # dealer_ids placeholder "raj" in scenario resolves to dealer1.dealer_id
    url = (
        "/api/v1/reports/sales"
        "?date_from=2026-06-01"
        "&date_to=2026-06-30"
        f"&dealer_ids={dealer1.dealer_id}"
        "&places=Mysuru"
    )
    resp = client.get(url)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "transactions" in body, "Response must contain 'transactions' key"
    assert "consolidation" in body, "Response must contain 'consolidation' key"

    transactions = body["transactions"]
    consolidation = body["consolidation"]

    # ------------------------------------------------------------------ transactions assertions
    # 4 lines: 2 lines from sale-1 (Jun 5) + 2 lines from sale-2 (Jun 15)
    assert len(transactions) == 4, (
        f"Expected 4 transaction lines (2 from sale-1 + 2 from sale-2), got {len(transactions)}"
    )

    # RULE-020: transactions ordered by sales_date ASC
    txn_dates = [date.fromisoformat(r["sales_date"]) for r in transactions]
    assert txn_dates == sorted(txn_dates), (
        f"Transactions not in sales_date ASC order: {txn_dates}"
    )

    # Bengaluru sale (dealer2) must be absent
    txn_dealer_ids = {r["dealer_id"] for r in transactions}
    assert dealer2.dealer_id not in txn_dealer_ids, (
        f"Bengaluru sale (dealer2={dealer2.dealer_id}) must be absent from transactions"
    )

    # July sale (date 2026-07-02) must be absent
    for txn in transactions:
        txn_date = date.fromisoformat(txn["sales_date"])
        assert txn_date <= date(2026, 6, 30), (
            f"July sale must be excluded, got sales_date={txn_date}"
        )

    # ------------------------------------------------------------------ consolidation assertions
    # 3 groups by (design, grade):
    # • 16X10 Ridges / G1: 10 + 6 = 16 total_nos
    # • 16X10 Ridges / G2: 8 total_nos
    # • 12X8 Ridges  / G2: 4 total_nos
    assert len(consolidation) == 3, (
        f"Expected 3 consolidation groups, got {len(consolidation)}: {consolidation}"
    )

    # RULE-019: consolidation ordered by design_name ASC, grade_code ASC
    # Expected sort: 12X8 Ridges/2 < 16X10 Ridges/1 < 16X10 Ridges/2
    expected_consolidation = [
        {"design_name": "12X8 Ridges",  "grade_code": "2", "total_nos": 4},
        {"design_name": "16X10 Ridges", "grade_code": "1", "total_nos": 16},
        {"design_name": "16X10 Ridges", "grade_code": "2", "total_nos": 8},
    ]
    for i, (row, exp) in enumerate(zip(consolidation, expected_consolidation)):
        assert row["design_name"] == exp["design_name"], (
            f"Consolidation row {i}: design_name expected={exp['design_name']!r}, got={row['design_name']!r}"
        )
        assert row["grade_code"] == exp["grade_code"], (
            f"Consolidation row {i}: grade_code expected={exp['grade_code']!r}, got={row['grade_code']!r}"
        )
        assert row["total_nos"] == exp["total_nos"], (
            f"Consolidation row {i} ({exp['design_name']}/{exp['grade_code']}): "
            f"total_nos expected={exp['total_nos']}, got={row['total_nos']}"
        )

    # ------------------------------------------------------------------ AC-050 reconciliation
    txn_sum = sum(r["nos"] for r in transactions)
    consol_sum = sum(r["total_nos"] for r in consolidation)
    assert txn_sum == 28, f"Expected transactions sum=28, got {txn_sum}"
    assert consol_sum == 28, f"Expected consolidation sum=28, got {consol_sum}"
    assert txn_sum == consol_sum, (
        f"AC-050 violated: sum(transactions.nos)={txn_sum} != sum(consolidation.total_nos)={consol_sum}"
    )
