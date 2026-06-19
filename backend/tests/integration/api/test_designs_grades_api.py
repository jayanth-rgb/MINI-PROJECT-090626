"""API contract tests for GET /api/v1/designs/{design_id}/grades (DF-006).

Covers: TC-036, TC-037.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def test_tc036_get_designs_grades_returns_active_projection(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        TradingDesignModel(
            design_id=10, size="16X10", design_name="16X10 Ridges", is_active=True
        )
    )
    db_session.add(GradeModel(grade_id=1, grade_code="1", is_active=True))
    db_session.add(GradeModel(grade_id=2, grade_code="2", is_active=True))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=10, grade_id=1, is_active=True))
    db_session.add(DesignGradeMapModel(design_id=10, grade_id=2, is_active=False))
    db_session.commit()

    response = client.get("/api/v1/designs/10/grades")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body == [{"grade_id": 1, "grade_code": "1"}]
    assert set(body[0].keys()) == {"grade_id", "grade_code"}


def test_tc037_get_designs_grades_empty_mappings_returns_empty_list(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        TradingDesignModel(
            design_id=20, size="12X8", design_name="12X8 Ridges", is_active=True
        )
    )
    db_session.commit()

    response = client.get("/api/v1/designs/20/grades")

    assert response.status_code == 200
    assert response.json() == []
    assert len(response.json()) == 0
