"""TC-070 — DesignGradeCbService (DF-003)."""
from __future__ import annotations

from datetime import date

import pytest

from src.application.services.design_grade_cb_service import DesignGradeCbService
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def _seed_two_grades(session) -> dict:
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    g1 = GradeModel(grade_code="1")
    g2 = GradeModel(grade_code="OB")
    session.add_all([design, g1, g2])
    session.flush()
    session.add_all([
        DesignGradeMapModel(design_id=design.design_id, grade_id=g1.grade_id),
        DesignGradeMapModel(design_id=design.design_id, grade_id=g2.grade_id),
    ])
    session.flush()
    return {
        "design_id": design.design_id,
        "g1_id": g1.grade_id,
        "g2_id": g2.grade_id,
    }


def test_tc070_list_active_grades_with_cb_projects_software_cb_per_active_mapping(db_session):
    """AC-036 — each active (design, grade) mapping projected with software_cb."""
    svc = DesignGradeCbService(db_session)
    ids = _seed_two_grades(db_session)
    # Seed running balances for both grades
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(
        db_session, ids["design_id"], ids["g1_id"], date(2026, 6, 1), 42, 1, 1
    )
    stock_mod.apply_inward(
        db_session, ids["design_id"], ids["g2_id"], date(2026, 6, 1), 17, 2, 1
    )
    db_session.commit()
    result = svc.list_active_grades_with_cb(ids["design_id"], date(2026, 6, 2))
    assert len(result) == 2
    by_id = {r.grade_id: r for r in result}
    assert by_id[ids["g1_id"]].software_cb == 42
    assert by_id[ids["g1_id"]].grade_code == "1"
    assert by_id[ids["g2_id"]].software_cb == 17
    assert by_id[ids["g2_id"]].grade_code == "OB"
