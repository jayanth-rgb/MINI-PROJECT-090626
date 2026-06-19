"""Unit tests for SupplierService (F-001).

Covers: TC-001, TC-004, TC-005, TC-006.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.supplier_service import SupplierService
from src.infrastructure.db.models.master import SupplierModel
from src.presentation.schemas.master import SupplierCreate


def _reset_supplier_seq(session: Session, to: int = 1) -> None:
    session.execute(
        text(f"ALTER SEQUENCE tbl_supplier_master_supplier_id_seq RESTART WITH {to}")
    )


def test_tc001_create_supplier_persists_row_and_returns_supplier_read(
    db_session: Session,
) -> None:
    _reset_supplier_seq(db_session, 1)
    service = SupplierService(db_session)
    payload = SupplierCreate(supplier_name="Manjunatha", place="Mallur")

    result = service.create_supplier(payload)

    assert result.supplier_id == 1
    assert result.supplier_name == "Manjunatha"
    assert result.place == "Mallur"
    assert result.is_active is True


def test_tc004_deactivate_supplier_sets_is_active_false_row_preserved(
    db_session: Session,
) -> None:
    seed = SupplierModel(
        supplier_id=7,
        supplier_name="Antony Tiles",
        place="Kerala",
        is_active=True,
    )
    db_session.add(seed)
    db_session.flush()
    service = SupplierService(db_session)

    result = service.deactivate_supplier(7)

    assert result.supplier_id == 7
    assert result.is_active is False
    row = db_session.get(SupplierModel, 7)
    assert row is not None
    assert row.is_active is False


def test_tc005_list_suppliers_default_excludes_inactive(db_session: Session) -> None:
    db_session.add(
        SupplierModel(supplier_id=1, supplier_name="A", place="X", is_active=True)
    )
    db_session.add(
        SupplierModel(supplier_id=2, supplier_name="B", place="Y", is_active=False)
    )
    db_session.flush()
    service = SupplierService(db_session)

    result = service.list_suppliers()

    ids = [r.supplier_id for r in result]
    assert ids == [1]
    assert len(result) == 1


def test_tc006_list_suppliers_include_inactive_returns_both(
    db_session: Session,
) -> None:
    db_session.add(
        SupplierModel(supplier_id=1, supplier_name="A", place="X", is_active=True)
    )
    db_session.add(
        SupplierModel(supplier_id=2, supplier_name="B", place="Y", is_active=False)
    )
    db_session.flush()
    service = SupplierService(db_session)

    result = service.list_suppliers(include_inactive=True)

    ids = sorted(r.supplier_id for r in result)
    assert ids == [1, 2]
    assert len(result) == 2
