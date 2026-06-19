"""Unit tests for DesignGradeMapService (F-006).

Covers: TC-019, TC-024, TC-025, TC-027, TC-028, TC-029, TC-031, TC-032.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.application.services.design_grade_map_service import DesignGradeMapService
from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.presentation.schemas.master import DesignGradeMapCreate


def _seed_design(session: Session, design_id: int) -> TradingDesignModel:
    obj = TradingDesignModel(
        design_id=design_id,
        size=f"size-{design_id}",
        design_name=f"design-{design_id}",
        is_active=True,
    )
    session.add(obj)
    session.flush()
    return obj


def _seed_grade(
    session: Session, grade_id: int, grade_code: str, is_active: bool = True
) -> GradeModel:
    obj = GradeModel(grade_id=grade_id, grade_code=grade_code, is_active=is_active)
    session.add(obj)
    session.flush()
    return obj


def _seed_mapping(
    session: Session,
    design_id: int,
    grade_id: int,
    is_active: bool = True,
    map_id: int | None = None,
) -> DesignGradeMapModel:
    kwargs = {"design_id": design_id, "grade_id": grade_id, "is_active": is_active}
    if map_id is not None:
        kwargs["map_id"] = map_id
    obj = DesignGradeMapModel(**kwargs)
    session.add(obj)
    session.flush()
    return obj


def test_tc019_list_active_grades_excludes_inactive_grade_via_join_filter(
    db_session: Session,
) -> None:
    _seed_design(db_session, 10)
    _seed_grade(db_session, 1, "1", is_active=True)
    _seed_grade(db_session, 2, "2", is_active=False)
    _seed_mapping(db_session, 10, 1, is_active=True)
    _seed_mapping(db_session, 10, 2, is_active=True)
    service = DesignGradeMapService(db_session)

    result = service.list_active_grades_for_design(10)

    assert len(result) == 1
    assert result[0].grade_id == 1
    assert result[0].grade_code == "1"


def test_tc024_create_mapping_persists_pair(db_session: Session) -> None:
    _seed_design(db_session, 10)
    _seed_grade(db_session, 1, "1", is_active=True)
    service = DesignGradeMapService(db_session)

    result = service.create_mapping(
        DesignGradeMapCreate(design_id=10, grade_id=1)
    )

    assert result.design_id == 10
    assert result.grade_id == 1
    assert result.is_active is True
    assert result.map_id is not None and result.map_id > 0


def test_tc025_create_mapping_duplicate_pair_raises_conflict_error(
    db_session: Session,
) -> None:
    _seed_design(db_session, 10)
    _seed_grade(db_session, 1, "1", is_active=True)
    _seed_mapping(db_session, 10, 1, is_active=True)
    service = DesignGradeMapService(db_session)

    with pytest.raises(ConflictError) as exc_info:
        service.create_mapping(DesignGradeMapCreate(design_id=10, grade_id=1))

    assert "design_id, grade_id" in exc_info.value.message


def test_tc027_create_mapping_missing_design_raises_not_found_trading_design(
    db_session: Session,
) -> None:
    _seed_grade(db_session, 1, "1", is_active=True)
    service = DesignGradeMapService(db_session)

    with pytest.raises(NotFoundError) as exc_info:
        service.create_mapping(DesignGradeMapCreate(design_id=99999, grade_id=1))

    assert exc_info.value.entity == "TradingDesign"


def test_tc028_create_mapping_missing_grade_raises_not_found_grade(
    db_session: Session,
) -> None:
    _seed_design(db_session, 10)
    service = DesignGradeMapService(db_session)

    with pytest.raises(NotFoundError) as exc_info:
        service.create_mapping(DesignGradeMapCreate(design_id=10, grade_id=99999))

    assert exc_info.value.entity == "Grade"


def test_tc029_deactivate_mapping_soft_deletes_row_preserved(
    db_session: Session,
) -> None:
    _seed_design(db_session, 10)
    _seed_grade(db_session, 1, "1", is_active=True)
    _seed_mapping(db_session, 10, 1, is_active=True, map_id=5)
    service = DesignGradeMapService(db_session)

    result = service.deactivate_mapping(5)

    assert result.is_active is False
    row = db_session.get(DesignGradeMapModel, 5)
    assert row is not None
    assert row.is_active is False


def test_tc031_list_active_grades_returns_only_active_mappings_projection(
    db_session: Session,
) -> None:
    _seed_design(db_session, 10)
    _seed_grade(db_session, 1, "1", is_active=True)
    _seed_grade(db_session, 2, "2", is_active=True)
    _seed_mapping(db_session, 10, 1, is_active=True)
    _seed_mapping(db_session, 10, 2, is_active=False)
    service = DesignGradeMapService(db_session)

    result = service.list_active_grades_for_design(10)

    assert len(result) == 1
    assert result[0].grade_id == 1
    assert result[0].grade_code == "1"


def test_tc032_list_active_grades_empty_when_no_mappings(
    db_session: Session,
) -> None:
    _seed_design(db_session, 20)
    service = DesignGradeMapService(db_session)

    result = service.list_active_grades_for_design(20)

    assert result == []
    assert len(result) == 0
