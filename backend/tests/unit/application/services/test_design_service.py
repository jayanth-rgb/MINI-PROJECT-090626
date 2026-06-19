"""Unit tests for DesignService (F-005).

Covers: TC-020, TC-023.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.design_service import DesignService
from src.infrastructure.db.models.master import TradingDesignModel
from src.presentation.schemas.master import DesignCreate


def _reset_design_seq(session: Session, to: int = 1) -> None:
    session.execute(
        text(
            f"ALTER SEQUENCE tbl_trading_design_master_design_id_seq RESTART WITH {to}"
        )
    )


def test_tc020_create_design_persists_row_and_returns_design_read(
    db_session: Session,
) -> None:
    _reset_design_seq(db_session, 1)
    service = DesignService(db_session)
    payload = DesignCreate(size="16X10", design_name="16X10 Ridges")

    result = service.create_design(payload)

    assert result.design_id == 1
    assert result.size == "16X10"
    assert result.design_name == "16X10 Ridges"
    assert result.is_active is True


def test_tc023_deactivate_design_hides_from_default_list(db_session: Session) -> None:
    db_session.add(
        TradingDesignModel(
            design_id=3,
            size="11X7",
            design_name="11X7 Ridges",
            is_active=True,
        )
    )
    db_session.flush()
    service = DesignService(db_session)

    service.deactivate_design(3)

    active = service.list_designs()
    assert all(d.design_id != 3 for d in active)
    row = db_session.get(TradingDesignModel, 3)
    assert row is not None
    assert row.is_active is False
