"""DB-level UNIQUE(design_id, grade_id) composite constraint test.

Covers: TC-026.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def test_tc026_duplicate_design_grade_pair_raises_integrity_error(
    db_session: Session,
) -> None:
    db_session.add(
        TradingDesignModel(
            design_id=1, size="16X10", design_name="16X10 Ridges", is_active=True
        )
    )
    db_session.add(GradeModel(grade_id=1, grade_code="1", is_active=True))
    db_session.flush()

    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1, is_active=True))
    db_session.flush()

    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1, is_active=True))
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()

    err = str(exc_info.value).lower() + str(exc_info.value.orig).lower()
    assert "uq_design_grade_map_design_grade" in err
