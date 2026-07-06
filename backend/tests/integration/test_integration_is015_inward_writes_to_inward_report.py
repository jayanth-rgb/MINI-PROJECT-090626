"""IS-015 — DF-InwardReport: POST /inward writes → GET /reports/inward reconciled dual payload.

Verifies the M-002 → M-009 read composition and the DS-017 shared filter
predicate: filter narrows both sections identically, so the reconciliation
invariant sum(transactions.nos) == sum(consolidation.total_nos) holds under
any filter set, and no filter equals the full dataset.

Dates are today-1 / today-2 to stay inside AC-021's 7-day backdate window.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def test_is015(client, db_session):
    # ------------------------------------------------------------------ seed master
    d1 = TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges")
    d2 = TradingDesignModel(design_id=2, size="12X8", design_name="12X8 Ridges")
    g1 = GradeModel(grade_id=1, grade_code="1")
    g2 = GradeModel(grade_id=2, grade_code="2")
    s1 = SupplierModel(supplier_id=1, supplier_name="Manjunatha", place="Mallur")
    s2 = SupplierModel(supplier_id=2, supplier_name="Ravi Traders", place="Bengaluru")
    staff = StaffModel(staff_id=1, staff_name="Chandran")
    db_session.add_all([d1, d2, g1, g2, s1, s2, staff])
    db_session.flush()
    for design_id in (1, 2):
        for grade_id in (1, 2):
            db_session.add(
                DesignGradeMapModel(
                    design_id=design_id, grade_id=grade_id, is_active=True
                )
            )
    db_session.flush()

    date_a = (date.today() - timedelta(days=1)).isoformat()
    date_b = (date.today() - timedelta(days=2)).isoformat()

    # ---------------------------------------------- STEP 1 — inward from S1 @ Mallur, 2 lines
    resp1 = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date_a,
            "supplier_id": 1,
            "entered_by_id": 1,
            "lines": [
                {"design_id": 1, "grade_id": 1, "nos": 20},
                {"design_id": 1, "grade_id": 2, "nos": 10},
            ],
        },
    )
    assert resp1.status_code == 201, f"inward1 failed: {resp1.text}"

    # ---------------------------------------------- STEP 2 — inward from S1 @ Mallur, 1 line
    resp2 = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date_a,
            "supplier_id": 1,
            "entered_by_id": 1,
            "lines": [{"design_id": 2, "grade_id": 1, "nos": 5}],
        },
    )
    assert resp2.status_code == 201, f"inward2 failed: {resp2.text}"

    # ---------------------------------------------- STEP 3 — inward from S2 @ Bengaluru (filtered out below)
    resp3 = client.post(
        "/api/v1/inward",
        json={
            "purchase_date": date_b,
            "supplier_id": 2,
            "entered_by_id": 1,
            "lines": [{"design_id": 1, "grade_id": 1, "nos": 15}],
        },
    )
    assert resp3.status_code == 201, f"inward3 failed: {resp3.text}"

    # ---------------------------------------------- STEP 4 — filtered report (supplier=1, place=Mallur)
    resp_filtered = client.get(
        "/api/v1/reports/inward",
        params={"supplier_ids": 1, "places": "Mallur"},
    )
    assert resp_filtered.status_code == 200, (
        f"GET /reports/inward filtered failed: {resp_filtered.text}"
    )
    body_f = resp_filtered.json()

    # Reconciliation invariant per DS-017
    consol_sum_f = sum(r["total_nos"] for r in body_f["consolidation"])
    txn_sum_f = sum(r["nos"] for r in body_f["transactions"])
    assert consol_sum_f == txn_sum_f == 35, (
        f"filtered reconciliation broke: consol={consol_sum_f}, txn={txn_sum_f}"
    )
    assert len(body_f["transactions"]) == 3, (
        f"expected 3 transaction rows for supplier 1, got {len(body_f['transactions'])}"
    )
    assert len(body_f["consolidation"]) == 3, (
        f"expected 3 consolidation groups, got {len(body_f['consolidation'])}"
    )
    # Bengaluru inward from step 3 excluded (would have place='Bengaluru')
    assert all(r["place"] == "Mallur" for r in body_f["transactions"]), (
        f"filter leak — non-Mallur place present: {body_f['transactions']}"
    )
    # Consolidation ordering: design_name ASC, then grade_code ASC (RULE-019 mirror)
    consol_order = [(r["design_name"], r["grade_code"]) for r in body_f["consolidation"]]
    assert consol_order == sorted(consol_order), (
        f"consolidation not sorted: {consol_order}"
    )
    # Transactions ordering: purchase_date ASC
    txn_dates = [r["purchase_date"] for r in body_f["transactions"]]
    assert txn_dates == sorted(txn_dates), (
        f"transactions not date-sorted: {txn_dates}"
    )

    # ---------------------------------------------- STEP 5 — unfiltered report (full dataset)
    resp_all = client.get("/api/v1/reports/inward")
    assert resp_all.status_code == 200, f"GET /reports/inward all failed: {resp_all.text}"
    body_all = resp_all.json()
    consol_sum_all = sum(r["total_nos"] for r in body_all["consolidation"])
    txn_sum_all = sum(r["nos"] for r in body_all["transactions"])
    assert consol_sum_all == txn_sum_all == 50, (
        f"unfiltered reconciliation broke: consol={consol_sum_all}, txn={txn_sum_all}"
    )
    assert len(body_all["transactions"]) == 4
    # Bengaluru row now present
    assert any(r["place"] == "Bengaluru" for r in body_all["transactions"])
