"""ST-003 — Soft-delete preserves rows (HLD R-005 mitigation).

After soft-deleting a supplier, grade, design, and design-grade-map via the
HTTP API, all 4 rows must still be SELECT-able by their PKs (no DELETE
happened). This is the backstop S2 reports rely on for historical joins.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    SupplierModel,
    TradingDesignModel,
)


def test_st003_soft_delete_preserves_4_rows(
    client: TestClient, db_session: Session
) -> None:
    # 1. Create one row of each type via API.
    r = client.post(
        "/api/v1/suppliers",
        json={"supplier_name": "Antony Tiles", "place": "Kerala"},
    )
    assert r.status_code == 201, r.text
    supplier_id = r.json()["supplier_id"]

    r = client.post("/api/v1/grades", json={"grade_code": "ST-003-G"})
    assert r.status_code == 201, r.text
    grade_id = r.json()["grade_id"]

    r = client.post(
        "/api/v1/designs",
        json={"size": "16X10", "design_name": "ST-003-Ridges"},
    )
    assert r.status_code == 201, r.text
    design_id = r.json()["design_id"]

    r = client.post(
        "/api/v1/design-grade-map",
        json={"design_id": design_id, "grade_id": grade_id},
    )
    assert r.status_code == 201, r.text
    map_id = r.json()["map_id"]

    # 2. Soft-delete all 4.
    for path in (
        f"/api/v1/suppliers/{supplier_id}",
        f"/api/v1/grades/{grade_id}",
        f"/api/v1/designs/{design_id}",
        f"/api/v1/design-grade-map/{map_id}",
    ):
        r = client.delete(path)
        assert r.status_code == 200, f"{path}: {r.text}"
        assert r.json()["is_active"] is False

    # 3. Each row is physically present with is_active=false.
    supplier = db_session.get(SupplierModel, supplier_id)
    assert supplier is not None
    assert supplier.is_active is False

    grade = db_session.get(GradeModel, grade_id)
    assert grade is not None
    assert grade.is_active is False

    design = db_session.get(TradingDesignModel, design_id)
    assert design is not None
    assert design.is_active is False

    mapping = db_session.get(DesignGradeMapModel, map_id)
    assert mapping is not None
    assert mapping.is_active is False
    # FK references still resolve — the historical join works.
    assert mapping.design_id == design_id
    assert mapping.grade_id == grade_id
