"""ST-012 — Soft-delete (is_active=False) removes pair from dashboard but
preserves it in Sales Report historical joins (AC-012, AC-017, R-005).

Three parts:
  (a) Pair is_active=True → GET /dashboard returns the pair (closing=80).
  (b) Set map.is_active=False → GET /dashboard must NOT include the pair.
  (c) Seed 1 sales_header + sales_line for the same deactivated pair.
      GET /reports/sales → the historical sale IS in transactions[] and
      consolidation[], proving FK joins are unaffected by is_active on the
      design-grade mapping (R-005 mitigation).

Seeding strategy:
  - Masters: TradingDesignModel("16X10 Ridges"), GradeModel("2"), DesignGradeMapModel
  - Historical ledger: 2 rows via direct ORM insert (bypasses InwardService so
    we are not subject to AC-021 backdate window):
      row 1: inward delta=+100, running_balance=100
      row 2: sale delta=-20,   running_balance=80
  - Historical sale: SalesHeaderModel + SalesLineModel (direct ORM insert).
"""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    DealerModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    SalesHeaderModel,
    SalesLineModel,
    StockLedgerModel,
)


def test_st012(client, db_session):
    """ST-012: Soft-delete hides pair from dashboard; historical sales still appear in reports."""
    # ------------------------------------------------------------------
    # (a) Seed masters
    # ------------------------------------------------------------------
    design = TradingDesignModel(
        design_name="16X10 Ridges", size="16X10", is_active=True
    )
    grade = GradeModel(grade_code="2", is_active=True)
    db_session.add_all([design, grade])
    db_session.flush()

    mapping = DesignGradeMapModel(
        design_id=design.design_id, grade_id=grade.grade_id, is_active=True
    )
    db_session.add(mapping)
    db_session.flush()

    # Seed historical ledger for this pair (ORM direct — bypasses backdate window).
    # Two historical months ago so as_of_date=today still picks them up as opening.
    historical_date_inward = date.today() - timedelta(days=60)
    historical_date_sale = date.today() - timedelta(days=59)

    ledger_inward = StockLedgerModel(
        design_id=design.design_id,
        grade_id=grade.grade_id,
        txn_date=historical_date_inward,
        source_type="inward",
        delta=100,
        running_balance=100,
        source_header_id=1,
        source_line_id=1,
    )
    ledger_sale = StockLedgerModel(
        design_id=design.design_id,
        grade_id=grade.grade_id,
        txn_date=historical_date_sale,
        source_type="sale",
        delta=-20,
        running_balance=80,
        source_header_id=2,
        source_line_id=1,
    )
    db_session.add_all([ledger_inward, ledger_sale])
    db_session.flush()

    today_iso = date.today().isoformat()

    # ------------------------------------------------------------------
    # (a) Dashboard with pair active → must show the pair, closing=80
    # ------------------------------------------------------------------
    resp = client.get(f"/api/v1/dashboard?as_of_date={today_iso}")
    assert resp.status_code == 200, (
        f"ST-012(a): GET /dashboard returned {resp.status_code}. Body: {resp.text}"
    )

    body = resp.json()
    active_pair_rows = [
        r for r in body
        if r["design_id"] == design.design_id and r["grade_id"] == grade.grade_id
    ]
    assert len(active_pair_rows) == 1, (
        f"ST-012(a) FAIL: expected the pair (design={design.design_id}, "
        f"grade={grade.grade_id}) in dashboard before deactivation, "
        f"found {len(active_pair_rows)} rows."
    )
    assert active_pair_rows[0]["closing"] == 80, (
        f"ST-012(a) FAIL: expected closing=80 for the pair before deactivation, "
        f"got closing={active_pair_rows[0]['closing']}."
    )

    # ------------------------------------------------------------------
    # (b) Deactivate the mapping
    # ------------------------------------------------------------------
    mapping.is_active = False
    db_session.flush()

    # Dashboard must NOT return the deactivated pair
    resp = client.get(f"/api/v1/dashboard?as_of_date={today_iso}")
    assert resp.status_code == 200, (
        f"ST-012(b): GET /dashboard returned {resp.status_code}. Body: {resp.text}"
    )

    body = resp.json()
    deactivated_pair_rows = [
        r for r in body
        if r["design_id"] == design.design_id and r["grade_id"] == grade.grade_id
    ]
    assert len(deactivated_pair_rows) == 0, (
        f"ST-012(b) FAIL: deactivated pair (design={design.design_id}, "
        f"grade={grade.grade_id}) still appears in dashboard after is_active=False. "
        f"DesignGradeMapRepository.list_active_all must filter on is_active=True."
    )

    # ------------------------------------------------------------------
    # (c) Seed a historical sale for the deactivated pair
    # ------------------------------------------------------------------
    loader = StaffModel(staff_name="ST012 Loader")
    verifier = StaffModel(staff_name="ST012 Verifier")
    db_session.add_all([loader, verifier])
    db_session.flush()

    dealer = DealerModel(dealer_name="ST012 Dealer", place="Mysuru", is_active=True)
    db_session.add(dealer)
    db_session.flush()

    # Historical sale date (within recorded history, outside 7-day backdate window —
    # we use direct ORM insert so AC-021 doesn't apply here)
    hist_sale_date = date.today() - timedelta(days=30)
    sale_header = SalesHeaderModel(
        sales_date=hist_sale_date,
        dealer_id=dealer.dealer_id,
        place="Mysuru",
        loading_staff_id=loader.staff_id,
        verified_by_id=verifier.staff_id,
    )
    db_session.add(sale_header)
    db_session.flush()

    sale_line = SalesLineModel(
        header_id=sale_header.header_id,
        design_id=design.design_id,
        grade_id=grade.grade_id,
        nos=20,
    )
    db_session.add(sale_line)
    db_session.flush()

    # GET /reports/sales — the historical sale must appear in both transactions[]
    # and consolidation[] even though the design-grade mapping is now is_active=False.
    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, (
        f"ST-012(c): GET /reports/sales returned {resp.status_code}. Body: {resp.text}"
    )

    report_body = resp.json()
    transactions = report_body.get("transactions", [])
    consolidation = report_body.get("consolidation", [])

    # Transactions: at least one row for this design+grade pair
    txn_for_pair = [
        t for t in transactions
        if t["design_id"] == design.design_id and t["grade_id"] == grade.grade_id
    ]
    assert len(txn_for_pair) >= 1, (
        f"ST-012(c) FAIL: historical sale for deactivated pair "
        f"(design={design.design_id}, grade={grade.grade_id}) not found in "
        f"transactions[]. R-005: soft-delete must NOT break historical reports. "
        f"Found {len(txn_for_pair)} matching rows."
    )
    assert txn_for_pair[0]["nos"] == 20, (
        f"ST-012(c) FAIL: expected nos=20, got nos={txn_for_pair[0]['nos']}."
    )

    # Consolidation: at least one row for this design+grade pair
    consol_for_pair = [
        c for c in consolidation
        if c["design_id"] == design.design_id and c["grade_id"] == grade.grade_id
    ]
    assert len(consol_for_pair) >= 1, (
        f"ST-012(c) FAIL: historical sale for deactivated pair "
        f"(design={design.design_id}, grade={grade.grade_id}) not found in "
        f"consolidation[]. R-005: soft-delete must NOT break historical reports. "
        f"Found {len(consol_for_pair)} matching rows."
    )
    assert consol_for_pair[0]["total_nos"] == 20, (
        f"ST-012(c) FAIL: expected total_nos=20, "
        f"got total_nos={consol_for_pair[0]['total_nos']}."
    )
