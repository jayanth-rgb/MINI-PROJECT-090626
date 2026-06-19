"""API contract tests for /api/v1/suppliers.

Covers: TC-033, TC-034.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import SupplierModel


def test_tc033_post_suppliers_returns_201_and_supplier_read_body(
    client: TestClient, db_session: Session
) -> None:
    response = client.post(
        "/api/v1/suppliers",
        json={"supplier_name": "Antony Tiles", "place": "Kerala"},
    )

    assert response.status_code == 201
    body = response.json()
    for key in ["supplier_id", "supplier_name", "place", "is_active", "created_at"]:
        assert key in body
    assert body["supplier_name"] == "Antony Tiles"
    assert body["place"] == "Kerala"
    assert body["is_active"] is True


def test_tc034_delete_suppliers_returns_200_with_deactivated_row_preserved(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        SupplierModel(
            supplier_id=1,
            supplier_name="Antony Tiles",
            place="Kerala",
            is_active=True,
        )
    )
    db_session.commit()

    response = client.delete("/api/v1/suppliers/1")

    assert response.status_code == 200
    body = response.json()
    assert body["supplier_id"] == 1
    assert body["is_active"] is False

    rows = db_session.execute(select(SupplierModel)).scalars().all()
    assert len(rows) == 1
    assert rows[0].supplier_id == 1
    assert rows[0].is_active is False
