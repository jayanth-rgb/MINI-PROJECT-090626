"""IS-001 — DF-006 end-to-end via the HTTP API.

Exercises the full chain M-006-style caller → designs / grades / design-grade-map
routers → DI → services → repos → ORM → testcontainer PG, then back via the
GET /api/v1/designs/{id}/grades projection.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_is001(client: TestClient) -> None:
    # 1. Seed design via API.
    r = client.post(
        "/api/v1/designs",
        json={"size": "16X10", "design_name": "16X10 Ridges"},
    )
    assert r.status_code == 201, r.text
    design_id = r.json()["design_id"]

    # 2. Seed two grades via API.
    grade_ids: list[int] = []
    for code in ("1", "OB"):
        r = client.post("/api/v1/grades", json={"grade_code": code})
        assert r.status_code == 201, r.text
        grade_ids.append(r.json()["grade_id"])

    # 3. Create both mappings via API.
    map_ids: list[int] = []
    for gid in grade_ids:
        r = client.post(
            "/api/v1/design-grade-map",
            json={"design_id": design_id, "grade_id": gid},
        )
        assert r.status_code == 201, r.text
        map_ids.append(r.json()["map_id"])

    # 4. Deactivate the second mapping.
    r = client.delete(f"/api/v1/design-grade-map/{map_ids[1]}")
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False

    # 5. GET projection — should contain only the first (active) mapping.
    r = client.get(f"/api/v1/designs/{design_id}/grades")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == [{"grade_id": grade_ids[0], "grade_code": "1"}]
    assert set(body[0].keys()) == {"grade_id", "grade_code"}
