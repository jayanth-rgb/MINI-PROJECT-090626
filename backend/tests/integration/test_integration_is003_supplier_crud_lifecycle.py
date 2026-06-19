"""IS-003 — Supplier CRUD round-trip end-to-end via the HTTP API.

Exercises router → DI → service → repo → ORM → testcontainer PG for the full
verb set (POST / GET / PATCH / DELETE / GET) chained as one user lifecycle.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_is003(client: TestClient) -> None:
    # 1. POST — create the supplier.
    r = client.post(
        "/api/v1/suppliers",
        json={"supplier_name": "Antony Tiles", "place": "Kerala"},
    )
    assert r.status_code == 201, r.text
    created = r.json()
    supplier_id = created["supplier_id"]
    assert created["place"] == "Kerala"
    assert created["is_active"] is True

    # 2. GET default — list contains the new row.
    r = client.get("/api/v1/suppliers")
    assert r.status_code == 200, r.text
    ids = [s["supplier_id"] for s in r.json()]
    assert supplier_id in ids

    # 3. PATCH — update place.
    r = client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        json={"place": "Trivandrum"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["place"] == "Trivandrum"
    assert r.json()["is_active"] is True

    # 4. DELETE — soft delete.
    r = client.delete(f"/api/v1/suppliers/{supplier_id}")
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False
    assert r.json()["place"] == "Trivandrum"

    # 5. GET default — soft-deleted row hidden.
    r = client.get("/api/v1/suppliers")
    assert r.status_code == 200
    ids = [s["supplier_id"] for s in r.json()]
    assert supplier_id not in ids

    # 6. GET include_inactive=true — row visible with is_active=false.
    r = client.get("/api/v1/suppliers?include_inactive=true")
    assert r.status_code == 200
    rows = {s["supplier_id"]: s for s in r.json()}
    assert supplier_id in rows
    assert rows[supplier_id]["is_active"] is False
    assert rows[supplier_id]["place"] == "Trivandrum"
