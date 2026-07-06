"""ST-023 — POST /prices with duplicate (design_id, grade_id, effective_from) returns 409 (AC-067)."""
from __future__ import annotations

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def _seed_masters(db_session):
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1))
    db_session.flush()


def test_st023_duplicate_price_returns_409(client, db_session):
    _seed_masters(db_session)
    body = {
        "design_id": 1,
        "grade_id": 1,
        "unit_price": "150.00",
        "effective_from": "2026-01-01",
    }
    first = client.post("/api/v1/prices", json=body)
    assert first.status_code == 201, f"first POST /prices failed: {first.text}"

    dup = client.post("/api/v1/prices", json=body)
    assert dup.status_code == 409, (
        f"duplicate price expected 409, got {dup.status_code}: {dup.text}"
    )
    # No Python stack trace should leak through
    assert "Traceback" not in dup.text
