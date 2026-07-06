"""V2 TC-214 — GET /reports/inward with Bearer JWT returns dual-payload response."""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    GradeModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    InwardHeaderModel,
    InwardLineModel,
)

from tests.integration.v2._helpers import bearer, seed_staff, seed_user


def test_tc214_get_inward_report_returns_200_with_reconciled_payload(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.add(SupplierModel(supplier_id=1, supplier_name="Manjunatha", place="Mallur"))
    seed_staff(db_session)
    db_session.flush()
    db_session.add(
        InwardHeaderModel(
            header_id=1,
            purchase_date=date(2026, 7, 1),
            supplier_id=1,
            place="Mallur",
            entered_by_id=1,
        )
    )
    db_session.flush()
    db_session.add(
        InwardLineModel(header_id=1, design_id=1, grade_id=1, nos=80)
    )
    db_session.flush()

    resp = client.get(
        "/api/v1/reports/inward",
        headers=bearer("admin", "SUPERVISOR"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["consolidation"]) >= 1
    assert len(body["transactions"]) >= 1
    consol_sum = sum(r["total_nos"] for r in body["consolidation"])
    txn_sum = sum(r["nos"] for r in body["transactions"])
    assert consol_sum == txn_sum
