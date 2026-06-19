"""API contract test for POST /api/v1/design-grade-map — duplicate pair → 409.

Covers: TC-038.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def test_tc038_post_design_grade_map_duplicate_pair_returns_409(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        TradingDesignModel(
            design_id=10, size="16X10", design_name="16X10 Ridges", is_active=True
        )
    )
    db_session.add(GradeModel(grade_id=1, grade_code="1", is_active=True))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=10, grade_id=1, is_active=True))
    db_session.commit()

    response = client.post(
        "/api/v1/design-grade-map",
        json={"design_id": 10, "grade_id": 1},
    )

    assert response.status_code == 409
    detail = response.json().get("detail", "")
    assert "design_id, grade_id" in detail
