"""TC-071 — GET /api/v1/designs/{id}/grades-with-cb (T-055 route)."""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def test_tc071_get_grades_with_cb_returns_projection(client, db_session):
    design = TradingDesignModel(size="16X10", design_name="D")
    g1 = GradeModel(grade_code="1")
    g2 = GradeModel(grade_code="OB")
    db_session.add_all([design, g1, g2])
    db_session.flush()
    db_session.add_all([
        DesignGradeMapModel(design_id=design.design_id, grade_id=g1.grade_id),
        DesignGradeMapModel(design_id=design.design_id, grade_id=g2.grade_id),
    ])
    # Seed balances via domain
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(
        db_session, design.design_id, g1.grade_id, date(2026, 6, 1), 42, 1, 1
    )
    stock_mod.apply_inward(
        db_session, design.design_id, g2.grade_id, date(2026, 6, 1), 17, 2, 1
    )
    db_session.commit()
    resp = client.get(
        f"/api/v1/designs/{design.design_id}/grades-with-cb",
        params={"stock_date": "2026-06-02"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    by_id = {row["grade_id"]: row for row in body}
    assert set(by_id[g1.grade_id].keys()) == {"grade_id", "grade_code", "software_cb"}
    assert by_id[g1.grade_id]["software_cb"] == 42
    assert by_id[g2.grade_id]["software_cb"] == 17
