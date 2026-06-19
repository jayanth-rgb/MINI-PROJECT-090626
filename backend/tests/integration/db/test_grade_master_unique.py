"""DB-level UNIQUE(grade_code) constraint test.

Covers: TC-018.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import GradeModel


def test_tc018_duplicate_grade_code_raises_integrity_error(db_session: Session) -> None:
    db_session.add(GradeModel(grade_code="DIM"))
    db_session.flush()

    db_session.add(GradeModel(grade_code="DIM"))
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()

    assert "uq_grade_master_grade_code" in str(exc_info.value).lower() or \
        "uq_grade_master_grade_code" in str(exc_info.value.orig).lower()
