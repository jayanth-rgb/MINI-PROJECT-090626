"""Unit tests for DealerService (F-003).

Covers: TC-012, TC-014.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.dealer_service import DealerService
from src.infrastructure.db.models.master import DealerModel
from src.presentation.schemas.master import DealerCreate


def _reset_dealer_seq(session: Session, to: int = 1) -> None:
    session.execute(
        text(f"ALTER SEQUENCE tbl_dealer_master_dealer_id_seq RESTART WITH {to}")
    )


def test_tc012_create_dealer_persists_row_and_returns_dealer_read(
    db_session: Session,
) -> None:
    _reset_dealer_seq(db_session, 1)
    service = DealerService(db_session)
    payload = DealerCreate(dealer_name="Raj Hardwares", place="Dindivanam")

    result = service.create_dealer(payload)

    assert result.dealer_id == 1
    assert result.dealer_name == "Raj Hardwares"
    assert result.place == "Dindivanam"
    assert result.is_active is True


def test_tc014_deactivate_dealer_hides_from_default_list(db_session: Session) -> None:
    db_session.add(
        DealerModel(
            dealer_id=5,
            dealer_name="Tiles Mart",
            place="Attibelle",
            is_active=True,
        )
    )
    db_session.flush()
    service = DealerService(db_session)

    service.deactivate_dealer(5)

    active = service.list_dealers()
    assert all(d.dealer_id != 5 for d in active)
    row = db_session.get(DealerModel, 5)
    assert row is not None
    assert row.is_active is False
