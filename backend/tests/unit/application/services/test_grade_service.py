"""Unit tests for GradeService (F-004).

Covers: TC-017.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.application.services.grade_service import GradeService
from src.domain.exceptions import ConflictError
from src.infrastructure.db.models.master import GradeModel
from src.presentation.schemas.master import GradeCreate


def test_tc017_create_grade_duplicate_code_raises_conflict_error(
    db_session: Session,
) -> None:
    db_session.add(GradeModel(grade_id=1, grade_code="1", is_active=True))
    db_session.flush()
    service = GradeService(db_session)

    with pytest.raises(ConflictError) as exc_info:
        service.create_grade(GradeCreate(grade_code="1"))

    assert "grade_code" in exc_info.value.message
