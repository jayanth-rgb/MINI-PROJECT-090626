"""IS-004 — AC-012 → AC-019 cross-feature: deactivating a Grade hides its
mappings from GET /designs/{id}/grades even when the mapping row itself is
still is_active=true. Enforced by the JOIN filter in T-006's
list_active_by_design.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import DesignGradeMapModel


def test_is004(client: TestClient, db_session: Session) -> None:
    # 1. POST design.
    r = client.post(
        "/api/v1/designs",
        json={"size": "12X8", "design_name": "12X8 Ridges"},
    )
    assert r.status_code == 201, r.text
    design_id = r.json()["design_id"]

    # 2. POST two grades.
    r = client.post("/api/v1/grades", json={"grade_code": "1"})
    assert r.status_code == 201, r.text
    grade1_id = r.json()["grade_id"]
    r = client.post("/api/v1/grades", json={"grade_code": "2"})
    assert r.status_code == 201, r.text
    grade2_id = r.json()["grade_id"]

    # 3. POST both mappings.
    for gid in (grade1_id, grade2_id):
        r = client.post(
            "/api/v1/design-grade-map",
            json={"design_id": design_id, "grade_id": gid},
        )
        assert r.status_code == 201, r.text

    # 4. Both grades visible in projection.
    r = client.get(f"/api/v1/designs/{design_id}/grades")
    assert r.status_code == 200
    grade_codes = sorted(g["grade_code"] for g in r.json())
    assert grade_codes == ["1", "2"]

    # 5. Deactivate grade '2'.
    r = client.delete(f"/api/v1/grades/{grade2_id}")
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False

    # 6. Projection now excludes grade '2', though its mapping row is still
    #    is_active=true (the JOIN filters on grade.is_active too).
    r = client.get(f"/api/v1/designs/{design_id}/grades")
    assert r.status_code == 200
    body = r.json()
    assert body == [{"grade_id": grade1_id, "grade_code": "1"}]

    # 7. The mapping (design_id, grade2_id) row still has is_active=true.
    mapping = db_session.execute(
        select(DesignGradeMapModel).where(
            DesignGradeMapModel.design_id == design_id,
            DesignGradeMapModel.grade_id == grade2_id,
        )
    ).scalar_one_or_none()
    assert mapping is not None
    assert mapping.is_active is True
