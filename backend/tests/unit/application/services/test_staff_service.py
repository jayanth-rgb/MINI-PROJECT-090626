"""Unit tests for StaffService (F-002).

Covers: TC-008, TC-010.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.staff_service import StaffService
from src.infrastructure.db.models.master import StaffModel
from src.presentation.schemas.master import StaffCreate


def _reset_staff_seq(session: Session, to: int = 1) -> None:
    session.execute(
        text(f"ALTER SEQUENCE tbl_staff_master_staff_id_seq RESTART WITH {to}")
    )


def test_tc008_create_staff_persists_row_and_returns_staff_read(
    db_session: Session,
) -> None:
    _reset_staff_seq(db_session, 1)
    service = StaffService(db_session)
    payload = StaffCreate(staff_name="Chandran")

    result = service.create_staff(payload)

    assert result.staff_id == 1
    assert result.staff_name == "Chandran"
    assert result.is_active is True


def test_tc010_deactivate_staff_hides_from_default_list(db_session: Session) -> None:
    db_session.add(StaffModel(staff_id=3, staff_name="Sujatha", is_active=True))
    db_session.flush()
    service = StaffService(db_session)

    service.deactivate_staff(3)

    active = service.list_staff()
    assert all(s.staff_id != 3 for s in active)
    row = db_session.get(StaffModel, 3)
    assert row is not None
    assert row.is_active is False
