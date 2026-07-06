"""V2 TC-187, TC-188, TC-189, TC-201..TC-206 — pricing repos + services integration.

Notes on spec vs code:
- TC-201 spec says HTTPException(409); PricingService follows the codebase's
  domain-exception convention (raises ConflictError, mapped to HTTP 409 by the
  global error handler in src/presentation/api/errors.py). We assert on
  ConflictError here — same behaviour, matches existing test convention.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.application.services.invoice_service import InvoiceService
from src.application.services.pricing_service import PricingService
from src.domain.exceptions import ConflictError
from src.infrastructure.db.models.pricing import (
    InvoiceHeaderModel,
    PaymentModel,
    PriceMasterModel,
)
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from src.infrastructure.db.repositories.pricing import (
    InvoiceRepository,
    PriceMasterRepository,
)
from src.presentation.schemas.pricing import PaymentCreate, PriceMasterCreate

from tests.integration.v2._helpers import (
    seed_dealer,
    seed_masters,
    seed_staff,
)


def _seed_prices(session, prices: list[dict]) -> None:
    for p in prices:
        session.add(
            PriceMasterModel(
                design_id=p["design_id"],
                grade_id=p["grade_id"],
                unit_price=Decimal(p["unit_price"]),
                effective_from=p["effective_from"],
                is_active=p["is_active"],
            )
        )
    session.flush()


def _seed_sales_order(session, header_id: int, sales_date: date, lines: list[dict]) -> None:
    session.add(
        SalesHeaderModel(
            header_id=header_id,
            sales_date=sales_date,
            dealer_id=1,
            place="Dindivanam",
            loading_staff_id=1,
            verified_by_id=1,
        )
    )
    session.flush()
    for line in lines:
        session.add(
            SalesLineModel(
                line_id=line["id"],
                header_id=header_id,
                design_id=line["design_id"],
                grade_id=line["grade_id"],
                nos=line["nos"],
            )
        )
    session.flush()


def test_tc187_get_active_price_returns_most_recent_effective_row(db_session):
    seed_masters(db_session)
    _seed_prices(
        db_session,
        [
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "100.00",
                "effective_from": date(2026, 1, 1),
                "is_active": True,
            },
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "120.00",
                "effective_from": date(2026, 6, 1),
                "is_active": True,
            },
        ],
    )
    row = PriceMasterRepository(db_session).get_active_price(1, 1)
    assert row is not None
    assert row.unit_price == Decimal("120.00")
    assert row.effective_from == date(2026, 6, 1)


def test_tc188_get_active_price_returns_none_when_only_row_inactive(db_session):
    seed_masters(db_session)
    _seed_prices(
        db_session,
        [
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "100.00",
                "effective_from": date(2026, 1, 1),
                "is_active": False,
            }
        ],
    )
    assert PriceMasterRepository(db_session).get_active_price(1, 1) is None


def test_tc189_create_with_lines_inserts_header_and_line_with_eager_loaded_lines(db_session):
    seed_masters(db_session)
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_sales_order(
        db_session,
        header_id=1,
        sales_date=date(2026, 7, 2),
        lines=[{"id": 1, "design_id": 1, "grade_id": 1, "nos": 5}],
    )
    repo = InvoiceRepository(db_session)
    invoice = repo.create_with_lines(
        header_data={
            "invoice_number": "INV-20260702-00001",
            "sales_header_id": 1,
            "invoice_date": date(2026, 7, 2),
            "total_amount": Decimal("500.00"),
            "status": "PENDING",
        },
        lines_data=[
            {
                "sales_line_id": 1,
                "design_id": 1,
                "grade_id": 1,
                "quantity": 5,
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("500.00"),
            }
        ],
    )
    assert invoice.invoice_number == "INV-20260702-00001"
    assert invoice.total_amount == Decimal("500.00")
    assert invoice.status == "PENDING"
    assert len(invoice.lines) == 1
    assert invoice.lines[0].line_total == Decimal("500.00")


def test_tc201_create_price_raises_conflict_when_triple_duplicate(db_session):
    seed_masters(db_session)
    _seed_prices(
        db_session,
        [
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "100.00",
                "effective_from": date(2026, 7, 1),
                "is_active": True,
            }
        ],
    )
    svc = PricingService(db_session)
    payload = PriceMasterCreate(
        design_id=1,
        grade_id=1,
        unit_price=Decimal("150.00"),
        effective_from=date(2026, 7, 1),
    )
    with pytest.raises(ConflictError):
        svc.create_price(payload)


def test_tc202_create_from_sales_snapshots_unit_prices_and_computes_total(db_session):
    seed_masters(
        db_session,
        designs=[(1, "16X10", "16X10 Ridges")],
        grades=[(1, "1"), (2, "2")],
    )
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_prices(
        db_session,
        [
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "100.00",
                "effective_from": date(2026, 1, 1),
                "is_active": True,
            },
            {
                "design_id": 1,
                "grade_id": 2,
                "unit_price": "80.00",
                "effective_from": date(2026, 1, 1),
                "is_active": True,
            },
        ],
    )
    _seed_sales_order(
        db_session,
        header_id=1,
        sales_date=date(2026, 7, 1),
        lines=[
            {"id": 1, "design_id": 1, "grade_id": 1, "nos": 10},
            {"id": 2, "design_id": 1, "grade_id": 2, "nos": 5},
        ],
    )
    svc = InvoiceService(db_session)
    invoice = svc.create_from_sales(1)
    assert invoice.total_amount == Decimal("1400.00")
    assert invoice.status == "PENDING"
    assert len(invoice.lines) == 2
    assert invoice.invoice_number.startswith("INV-")
    grade_to_line = {line.grade_id: line for line in invoice.lines}
    assert grade_to_line[1].unit_price == Decimal("100.00")
    assert grade_to_line[2].unit_price == Decimal("80.00")


def test_tc203_create_from_sales_raises_409_when_already_invoiced(db_session):
    seed_masters(db_session)
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_sales_order(
        db_session,
        header_id=1,
        sales_date=date(2026, 7, 1),
        lines=[{"id": 1, "design_id": 1, "grade_id": 1, "nos": 5}],
    )
    db_session.add(
        InvoiceHeaderModel(
            invoice_number="INV-20260701-00001",
            sales_header_id=1,
            invoice_date=date(2026, 7, 1),
            total_amount=Decimal("500.00"),
            status="PENDING",
        )
    )
    db_session.flush()

    svc = InvoiceService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        svc.create_from_sales(1)
    assert exc_info.value.status_code == 409


def test_tc204_invoice_line_unit_price_snapshot_survives_price_master_edit(db_session):
    seed_masters(db_session)
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_prices(
        db_session,
        [
            {
                "design_id": 1,
                "grade_id": 1,
                "unit_price": "100.00",
                "effective_from": date(2026, 1, 1),
                "is_active": True,
            }
        ],
    )
    _seed_sales_order(
        db_session,
        header_id=2,
        sales_date=date(2026, 7, 1),
        lines=[{"id": 3, "design_id": 1, "grade_id": 1, "nos": 5}],
    )
    svc = InvoiceService(db_session)
    invoice = svc.create_from_sales(2)
    invoice_id = invoice.id

    # Mutate the underlying price master row after invoice creation.
    price_row = db_session.query(PriceMasterModel).one()
    price_row.unit_price = Decimal("200.00")
    db_session.flush()
    db_session.commit()

    reloaded = svc.get_invoice(invoice_id)
    assert reloaded.lines[0].unit_price == Decimal("100.00")
    assert reloaded.lines[0].line_total == Decimal("500.00")


def test_tc205_record_payment_full_amount_transitions_to_paid(db_session):
    seed_masters(db_session)
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_sales_order(
        db_session,
        header_id=1,
        sales_date=date(2026, 7, 2),
        lines=[{"id": 1, "design_id": 1, "grade_id": 1, "nos": 5}],
    )
    header = InvoiceHeaderModel(
        invoice_number="INV-20260702-00001",
        sales_header_id=1,
        invoice_date=date(2026, 7, 2),
        total_amount=Decimal("500.00"),
        status="PENDING",
    )
    db_session.add(header)
    db_session.flush()

    svc = InvoiceService(db_session)
    result = svc.record_payment(
        header.id,
        PaymentCreate(payment_date=date(2026, 7, 2), amount=Decimal("500.00"), notes=None),
    )
    assert result.status == "PAID"
    assert len(result.payments) == 1
    assert result.payments[0].amount == Decimal("500.00")


def test_tc206_record_payment_overpayment_raises_422(db_session):
    seed_masters(db_session)
    seed_staff(db_session)
    seed_dealer(db_session)
    _seed_sales_order(
        db_session,
        header_id=1,
        sales_date=date(2026, 7, 2),
        lines=[{"id": 1, "design_id": 1, "grade_id": 1, "nos": 5}],
    )
    header = InvoiceHeaderModel(
        invoice_number="INV-20260702-00002",
        sales_header_id=1,
        invoice_date=date(2026, 7, 2),
        total_amount=Decimal("500.00"),
        status="PARTIAL",
    )
    db_session.add(header)
    db_session.flush()
    db_session.add(
        PaymentModel(
            invoice_header_id=header.id,
            payment_date=date(2026, 7, 1),
            amount=Decimal("400.00"),
            notes=None,
        )
    )
    db_session.flush()

    svc = InvoiceService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        svc.record_payment(
            header.id,
            PaymentCreate(
                payment_date=date(2026, 7, 2),
                amount=Decimal("200.00"),
                notes=None,
            ),
        )
    assert exc_info.value.status_code == 422
