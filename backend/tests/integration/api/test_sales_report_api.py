"""TC-133 to TC-142, TC-147, TC-148, TC-160 — Sales Report API integration tests (F-011).

Tests hit GET /api/v1/reports/sales using the `client` fixture (FastAPI TestClient
with real PostgreSQL via testcontainers). Each test seeds its own data through
`db_session` and rolls back after completion.

AC-050 reconciliation invariant: sum(transactions.nos) == sum(consolidation.total_nos)
is checked in TC-141 and TC-142.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DealerModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    SalesHeaderModel,
    SalesLineModel,
)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_staff(db):
    """Seed loader + verifier staff (required FKs on SalesHeaderModel)."""
    from src.infrastructure.db.models.master import StaffModel
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


# ---------------------------------------------------------------------------
# TC-133: no filters returns full dataset
# ---------------------------------------------------------------------------

def test_tc133_no_filters_returns_full_dataset(client, db_session):
    """Sales Report with no filters returns all sales lines + consolidation groupings.

    Seed: dealer_id=1 with 2 lines on 2026-06-05; dealer_id=2 with 1 line on 2026-06-10.
    Expected: consolidation_row_count=2 (2 distinct design+grade pairs),
              transaction_row_count=3 (3 sales lines total),
              both sums == 35.
    """
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")

    # Sale 1: dealer1, 2026-06-05, 2 lines
    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [
            {"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 10},
            {"design_id": design1.design_id, "grade_id": grade2.grade_id, "nos": 5},
        ],
    )
    # Sale 2: dealer2, 2026-06-10, 1 line
    _seed_sale(
        db_session, date(2026, 6, 10), dealer2.dealer_id, "Attibelle",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 20}],
    )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    consolidation = body["consolidation"]
    transactions = body["transactions"]

    # 2 distinct (design, grade) pairs: (design1, grade1) and (design1, grade2)
    assert len(consolidation) == 2, f"Expected 2 consolidation rows, got {len(consolidation)}"
    # 3 sales lines total
    assert len(transactions) == 3, f"Expected 3 transaction rows, got {len(transactions)}"

    consol_sum = sum(r["total_nos"] for r in consolidation)
    txn_sum = sum(r["nos"] for r in transactions)
    assert consol_sum == 35, f"Expected consolidation sum=35, got {consol_sum}"
    assert txn_sum == 35, f"Expected transaction sum=35, got {txn_sum}"


# ---------------------------------------------------------------------------
# TC-134: single dealer_ids=[1] filter
# ---------------------------------------------------------------------------

def test_tc134_single_dealer_filter_returns_only_that_dealer(client, db_session):
    """Sales Report with single dealer filter returns only that dealer's sales."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")

    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [
            {"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 10},
            {"design_id": design1.design_id, "grade_id": grade2.grade_id, "nos": 5},
        ],
    )
    _seed_sale(
        db_session, date(2026, 6, 10), dealer2.dealer_id, "Attibelle",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 20}],
    )

    resp = client.get(f"/api/v1/reports/sales?dealer_ids={dealer1.dealer_id}")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    transactions = body["transactions"]

    assert len(transactions) == 2, f"Expected 2 transactions for dealer1, got {len(transactions)}"
    dealer_ids_returned = {r["dealer_id"] for r in transactions}
    assert dealer_ids_returned == {dealer1.dealer_id}, (
        f"Expected only dealer_id={dealer1.dealer_id}, got {dealer_ids_returned}"
    )

    consol_sum = sum(r["total_nos"] for r in body["consolidation"])
    txn_sum = sum(r["nos"] for r in transactions)
    assert consol_sum == 15, f"Expected consolidation sum=15, got {consol_sum}"
    assert txn_sum == 15, f"Expected transaction sum=15, got {txn_sum}"


# ---------------------------------------------------------------------------
# TC-135: multi-select dealer_ids=[1, 2] includes union; excludes dealer 3
# ---------------------------------------------------------------------------

def test_tc135_multi_select_dealer_filter_returns_union(client, db_session):
    """Sales Report with dealer_ids=[1, 2] returns union; dealer 3 excluded."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    dealer3 = _seed_dealer(db_session, "Coimbatore Depot", "Coimbatore")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    design2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")
    grade3 = _seed_grade(db_session, "2A")

    # TC-133 seed
    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [
            {"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 10},
            {"design_id": design1.design_id, "grade_id": grade2.grade_id, "nos": 5},
        ],
    )
    _seed_sale(
        db_session, date(2026, 6, 10), dealer2.dealer_id, "Attibelle",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 20}],
    )
    # Extra: dealer3
    _seed_sale(
        db_session, date(2026, 6, 12), dealer3.dealer_id, "Coimbatore",
        loader_id, verifier_id,
        [{"design_id": design2.design_id, "grade_id": grade3.grade_id, "nos": 7}],
    )

    resp = client.get(
        f"/api/v1/reports/sales?dealer_ids={dealer1.dealer_id}&dealer_ids={dealer2.dealer_id}"
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    transactions = body["transactions"]

    assert len(transactions) == 3, f"Expected 3 transactions, got {len(transactions)}"
    dealer_ids_returned = sorted({r["dealer_id"] for r in transactions})
    assert dealer_ids_returned == sorted([dealer1.dealer_id, dealer2.dealer_id]), (
        f"Expected dealers {[dealer1.dealer_id, dealer2.dealer_id]}, got {dealer_ids_returned}"
    )
    # dealer3 must be absent
    assert dealer3.dealer_id not in {r["dealer_id"] for r in transactions}, (
        "dealer3 should be excluded from the result"
    )


# ---------------------------------------------------------------------------
# TC-136: all 5 filters combined returns intersection
# ---------------------------------------------------------------------------

def test_tc136_all_five_filters_return_intersection(client, db_session):
    """Sales Report with ALL 5 filters combined returns their intersection."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    dealer3 = _seed_dealer(db_session, "Depot C", "Chennai")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    design2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")

    # Rows that SHOULD match (date in range, dealer1, place=Dindivanam, design1)
    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 8}],
    )
    _seed_sale(
        db_session, date(2026, 6, 10), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade2.grade_id, "nos": 6}],
    )
    # Outside date range (2026-05-15 — before date_from=2026-06-01)
    _seed_sale(
        db_session, date(2026, 5, 15), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 100}],
    )
    # Wrong dealer (dealer3)
    _seed_sale(
        db_session, date(2026, 6, 8), dealer3.dealer_id, "Chennai",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 50}],
    )
    # Wrong design (design2)
    _seed_sale(
        db_session, date(2026, 6, 7), dealer2.dealer_id, "Attibelle",
        loader_id, verifier_id,
        [{"design_id": design2.design_id, "grade_id": grade1.grade_id, "nos": 30}],
    )

    resp = client.get(
        "/api/v1/reports/sales"
        "?date_from=2026-06-01"
        "&date_to=2026-06-15"
        f"&dealer_ids={dealer1.dealer_id}"
        f"&dealer_ids={dealer2.dealer_id}"
        "&places=Dindivanam"
        "&places=Attibelle"
        f"&design_ids={design1.design_id}"
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    transactions = body["transactions"]

    # Verify all 5 predicates applied
    for txn in transactions:
        sale_date = date.fromisoformat(txn["sales_date"])
        assert date(2026, 6, 1) <= sale_date <= date(2026, 6, 15), (
            f"Date {sale_date} outside [2026-06-01, 2026-06-15]"
        )
        assert txn["dealer_id"] in {dealer1.dealer_id, dealer2.dealer_id}, (
            f"dealer_id {txn['dealer_id']} not in filter set"
        )
        assert txn["place"] in {"Dindivanam", "Attibelle"}, (
            f"place {txn['place']} not in filter set"
        )
        assert txn["design_id"] == design1.design_id, (
            f"design_id {txn['design_id']} != {design1.design_id}"
        )


# ---------------------------------------------------------------------------
# TC-137: consolidation groups multiple sales of same pair into one row
# ---------------------------------------------------------------------------

def test_tc137_consolidation_groups_same_pair_into_one_row(client, db_session):
    """Consolidation rows GROUP BY (design_id, grade_id) and SUM(nos).

    3 sales of the same pair: nos=10, 15, 5 → 1 consolidation row, total_nos=30.
    """
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")

    for sale_date, nos in [
        (date(2026, 6, 5), 10),
        (date(2026, 6, 7), 15),
        (date(2026, 6, 10), 5),
    ]:
        _seed_sale(
            db_session, sale_date, dealer1.dealer_id, "Dindivanam",
            loader_id, verifier_id,
            [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": nos}],
        )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    consolidation = body["consolidation"]
    transactions = body["transactions"]

    assert len(consolidation) == 1, (
        f"Expected 1 consolidation row (same design+grade), got {len(consolidation)}"
    )
    assert consolidation[0]["total_nos"] == 30, (
        f"Expected total_nos=30, got {consolidation[0]['total_nos']}"
    )
    assert len(transactions) == 3, (
        f"Expected 3 transaction rows, got {len(transactions)}"
    )
    assert sum(r["nos"] for r in transactions) == 30


# ---------------------------------------------------------------------------
# TC-138: consolidation order is design_name ASC, grade_code ASC (RULE-019)
# ---------------------------------------------------------------------------

def test_tc138_consolidation_ordered_by_design_name_then_grade_code(client, db_session):
    """Consolidation ORDER BY design_name ASC, grade_code ASC regardless of insertion order."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")

    # Designs and grades for the 5 pairs
    design_16x10 = _seed_design(db_session, "16X10 Ridges", "16X10")
    design_11x7 = _seed_design(db_session, "11X7 Ridges", "11X7")
    design_12x8 = _seed_design(db_session, "12X8 Ridges", "12X8")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")
    grade_ob = _seed_grade(db_session, "OB")

    # Seed in non-alphabetical insertion order matching TC-138 spec
    pairs = [
        (design_16x10, grade2, 1),
        (design_11x7, grade1, 2),
        (design_16x10, grade1, 3),
        (design_12x8, grade_ob, 4),
        (design_12x8, grade1, 5),
    ]
    for design, grade, nos in pairs:
        _seed_sale(
            db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
            loader_id, verifier_id,
            [{"design_id": design.design_id, "grade_id": grade.grade_id, "nos": nos}],
        )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    consolidation = resp.json()["consolidation"]
    assert len(consolidation) == 5, f"Expected 5 consolidation rows, got {len(consolidation)}"

    # Expected order: 11X7 Ridges/1, 12X8 Ridges/1, 12X8 Ridges/OB, 16X10 Ridges/1, 16X10 Ridges/2
    expected_order = [
        ("11X7 Ridges", "1"),
        ("12X8 Ridges", "1"),
        ("12X8 Ridges", "OB"),
        ("16X10 Ridges", "1"),
        ("16X10 Ridges", "2"),
    ]
    for i, (exp_name, exp_grade) in enumerate(expected_order):
        assert consolidation[i]["design_name"] == exp_name, (
            f"Row {i}: expected design_name={exp_name}, got {consolidation[i]['design_name']}"
        )
        assert consolidation[i]["grade_code"] == exp_grade, (
            f"Row {i}: expected grade_code={exp_grade}, got {consolidation[i]['grade_code']}"
        )


# ---------------------------------------------------------------------------
# TC-139: transactions ordered by sales_date ASC, header_id ASC (RULE-020)
# ---------------------------------------------------------------------------

def test_tc139_transactions_ordered_by_sales_date_asc(client, db_session):
    """Transactions ORDER BY sales_date ASC; same-date ties break by header_id ASC."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")

    # Insert in non-chronological order matching TC-139 spec
    insert_dates = [
        date(2026, 6, 10),
        date(2026, 6, 3),
        date(2026, 6, 15),
        date(2026, 6, 3),   # duplicate date — tie-break by header_id
        date(2026, 6, 7),
    ]
    for sale_date in insert_dates:
        _seed_sale(
            db_session, sale_date, dealer1.dealer_id, "Dindivanam",
            loader_id, verifier_id,
            [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 1}],
        )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    transactions = resp.json()["transactions"]
    assert len(transactions) == 5, f"Expected 5 transactions, got {len(transactions)}"

    returned_dates = [date.fromisoformat(r["sales_date"]) for r in transactions]
    expected_dates = [
        date(2026, 6, 3),
        date(2026, 6, 3),
        date(2026, 6, 7),
        date(2026, 6, 10),
        date(2026, 6, 15),
    ]
    assert returned_dates == expected_dates, (
        f"Expected dates {expected_dates}, got {returned_dates}"
    )


# ---------------------------------------------------------------------------
# TC-140: both 'consolidation' and 'transactions' keys in single response
# ---------------------------------------------------------------------------

def test_tc140_response_has_both_consolidation_and_transactions_keys(client, db_session):
    """GET /reports/sales returns JSON with both 'consolidation' and 'transactions' keys."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")
    _seed_sale(
        db_session, date(2026, 6, 5), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 3}],
    )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "consolidation" in body, "Response must contain 'consolidation' key"
    assert "transactions" in body, "Response must contain 'transactions' key"
    # Single response (no pagination, no separate endpoints)
    assert isinstance(body["consolidation"], list)
    assert isinstance(body["transactions"], list)


# ---------------------------------------------------------------------------
# TC-141: AC-050 reconciliation invariant with no filters
# ---------------------------------------------------------------------------

def test_tc141_reconciliation_invariant_no_filters(client, db_session):
    """Reconciliation: sum(transactions.nos) == sum(consolidation.total_nos), no filters.

    Seed: 10 sales rows × 2 lines each, total nos = 537 (per TC-141 spec).
    """
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    design2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")

    # 10 headers × 2 lines each = 537 total nos
    # Using deterministic nos values that sum to 537 across 20 lines
    seed_data = [
        (date(2026, 6, 1),  dealer1.dealer_id, "Dindivanam", design1.design_id, grade1.grade_id, 35, design1.design_id, grade2.grade_id, 10),
        (date(2026, 6, 2),  dealer1.dealer_id, "Dindivanam", design1.design_id, grade1.grade_id, 40, design2.design_id, grade1.grade_id, 8),
        (date(2026, 6, 3),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade2.grade_id, 12, design2.design_id, grade2.grade_id, 25),
        (date(2026, 6, 4),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 50, design1.design_id, grade1.grade_id, 18),
        (date(2026, 6, 5),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 22, design1.design_id, grade2.grade_id, 16),
        (date(2026, 6, 6),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade2.grade_id, 35, design2.design_id, grade1.grade_id, 14),
        (date(2026, 6, 7),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 48, design1.design_id, grade2.grade_id, 17),
        (date(2026, 6, 8),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 40, design2.design_id, grade2.grade_id, 19),
        (date(2026, 6, 9),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 33, design1.design_id, grade2.grade_id, 21),
        (date(2026, 6, 10), dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 50, design2.design_id, grade2.grade_id, 24),
    ]
    # Total: 35+10+40+8+12+25+50+18+22+16+35+14+48+17+40+19+33+21+50+24 = 537
    expected_total = 537

    for row in seed_data:
        (sales_date, dealer_id, place,
         d1, g1, n1, d2, g2, n2) = row
        _seed_sale(
            db_session, sales_date, dealer_id, place,
            loader_id, verifier_id,
            [
                {"design_id": d1, "grade_id": g1, "nos": n1},
                {"design_id": d2, "grade_id": g2, "nos": n2},
            ],
        )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    txn_sum = sum(r["nos"] for r in body["transactions"])
    consol_sum = sum(r["total_nos"] for r in body["consolidation"])

    assert txn_sum == expected_total, (
        f"Expected transactions sum={expected_total}, got {txn_sum}"
    )
    assert consol_sum == expected_total, (
        f"Expected consolidation sum={expected_total}, got {consol_sum}"
    )
    assert txn_sum == consol_sum, (
        f"AC-050 invariant broken: txn_sum={txn_sum} != consol_sum={consol_sum}"
    )


# ---------------------------------------------------------------------------
# TC-142: AC-050 reconciliation invariant with ALL filters
# ---------------------------------------------------------------------------

def test_tc142_reconciliation_invariant_all_filters(client, db_session):
    """Reconciliation: sum(transactions.nos) == sum(consolidation.total_nos) with all filters.

    Same dataset as TC-141; applies date_from=2026-06-01, date_to=2026-06-10,
    dealer_ids=[dealer1], places=['Dindivanam'], design_ids=[design1].
    Window starts at 06-01 so the design1 lines on 06-01/02/04 (sole window matches
    for dealer1+Dindivanam+design1) are included — yields a non-trivial intersection
    that exercises AC-050 with > 0 rows.
    """
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    design2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    grade1 = _seed_grade(db_session, "1")
    grade2 = _seed_grade(db_session, "2")

    seed_data = [
        (date(2026, 6, 1),  dealer1.dealer_id, "Dindivanam", design1.design_id, grade1.grade_id, 15, design1.design_id, grade2.grade_id, 10),
        (date(2026, 6, 2),  dealer1.dealer_id, "Dindivanam", design1.design_id, grade1.grade_id, 20, design2.design_id, grade1.grade_id, 8),
        (date(2026, 6, 3),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade2.grade_id, 12, design2.design_id, grade2.grade_id, 25),
        (date(2026, 6, 4),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 30, design1.design_id, grade1.grade_id, 18),
        (date(2026, 6, 5),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 22, design1.design_id, grade2.grade_id, 16),
        (date(2026, 6, 6),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade2.grade_id, 35, design2.design_id, grade1.grade_id, 14),
        (date(2026, 6, 7),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 28, design1.design_id, grade2.grade_id, 17),
        (date(2026, 6, 8),  dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 40, design2.design_id, grade2.grade_id, 19),
        (date(2026, 6, 9),  dealer2.dealer_id, "Attibelle",  design1.design_id, grade1.grade_id, 33, design1.design_id, grade2.grade_id, 21),
        (date(2026, 6, 10), dealer1.dealer_id, "Dindivanam", design2.design_id, grade1.grade_id, 50, design2.design_id, grade2.grade_id, 24),
    ]
    for row in seed_data:
        (sales_date, dealer_id, place,
         d1, g1, n1, d2, g2, n2) = row
        _seed_sale(
            db_session, sales_date, dealer_id, place,
            loader_id, verifier_id,
            [
                {"design_id": d1, "grade_id": g1, "nos": n1},
                {"design_id": d2, "grade_id": g2, "nos": n2},
            ],
        )

    resp = client.get(
        "/api/v1/reports/sales"
        "?date_from=2026-06-01"
        "&date_to=2026-06-10"
        f"&dealer_ids={dealer1.dealer_id}"
        "&places=Dindivanam"
        f"&design_ids={design1.design_id}"
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    txn_sum = sum(r["nos"] for r in body["transactions"])
    consol_sum = sum(r["total_nos"] for r in body["consolidation"])

    # The key invariant: both sections must agree on total
    assert txn_sum == consol_sum, (
        f"AC-050 invariant broken with all filters: txn_sum={txn_sum} != consol_sum={consol_sum}"
    )
    # Sanity: at least some rows should have been matched
    assert txn_sum > 0, (
        "Expected at least some matching rows with this filter set"
    )


# ---------------------------------------------------------------------------
# TC-147: GET with no query params returns 200 + both keys
# ---------------------------------------------------------------------------

def test_tc147_no_query_params_returns_200_with_both_keys(client, db_session):
    """GET /api/v1/reports/sales with no query params returns HTTP 200 + full dataset."""
    # Minimal seed so response is non-trivial
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")
    _seed_sale(
        db_session, date(2026, 6, 15), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 5}],
    )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "consolidation" in body
    assert "transactions" in body


# ---------------------------------------------------------------------------
# TC-148: repeat-key dealer_ids list parsed as list[int] by FastAPI
# ---------------------------------------------------------------------------

def test_tc148_repeat_key_dealer_ids_parsed_as_list(client, db_session):
    """GET /reports/sales?dealer_ids=1&dealer_ids=2 — FastAPI parses as list[int]=[1,2]."""
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    dealer2 = _seed_dealer(db_session, "Sri Tiles", "Attibelle")
    dealer3 = _seed_dealer(db_session, "Depot C", "Chennai")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")

    # Seed rows for all 3 dealers
    for dealer, place in [
        (dealer1, "Dindivanam"),
        (dealer2, "Attibelle"),
        (dealer3, "Chennai"),
    ]:
        _seed_sale(
            db_session, date(2026, 6, 15), dealer.dealer_id, place,
            loader_id, verifier_id,
            [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 5}],
        )

    resp = client.get(
        f"/api/v1/reports/sales?dealer_ids={dealer1.dealer_id}&dealer_ids={dealer2.dealer_id}"
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    transactions = body["transactions"]

    # Only dealer1 and dealer2 rows returned
    assert len(transactions) == 2, (
        f"Expected 2 transactions (dealer1 + dealer2), got {len(transactions)}"
    )
    returned_dealer_ids = sorted(r["dealer_id"] for r in transactions)
    assert returned_dealer_ids == sorted([dealer1.dealer_id, dealer2.dealer_id]), (
        f"Expected dealer_ids {sorted([dealer1.dealer_id, dealer2.dealer_id])}, "
        f"got {returned_dealer_ids}"
    )
    # dealer3 excluded
    assert dealer3.dealer_id not in {r["dealer_id"] for r in transactions}


# ---------------------------------------------------------------------------
# TC-160: integration smoke — DI factory get_sales_report_service wired correctly
# ---------------------------------------------------------------------------

def test_tc160_integration_smoke_di_factory_wired(client, db_session):
    """Smoke: TestClient → real session → get_sales_report_service → query.

    Verifies GET /api/v1/reports/sales returns 200 with both payload keys,
    confirming the DI factory is correctly wired end-to-end.
    """
    # Minimal seed — just verify the endpoint exists and responds correctly
    loader_id, verifier_id = _seed_staff(db_session)
    dealer1 = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade1 = _seed_grade(db_session, "1")
    _seed_sale(
        db_session, date(2026, 6, 15), dealer1.dealer_id, "Dindivanam",
        loader_id, verifier_id,
        [{"design_id": design1.design_id, "grade_id": grade1.grade_id, "nos": 3}],
    )

    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "consolidation" in body, "DI factory did not wire service correctly"
    assert "transactions" in body, "DI factory did not wire service correctly"
    assert len(body["transactions"]) == 1, (
        f"Expected 1 transaction row from DI-wired service, got {len(body['transactions'])}"
    )
