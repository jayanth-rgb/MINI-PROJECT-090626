"""TC-058, 059, 060, 062, 063, 065 — SalesService (F-008)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.application.services.sales_service import SalesService
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel
from src.presentation.schemas.transactions import SalesCreate, SalesLineCreate


def _seed_sales_world(session) -> dict:
    dealer = DealerModel(dealer_name="Raj Hardwares", place="Dindivanam")
    loader = StaffModel(staff_name="Chandran")
    verifier = StaffModel(staff_name="Jayapal")
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_code="1")
    session.add_all([dealer, loader, verifier, design, grade])
    session.flush()
    session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    session.flush()
    return {
        "dealer_id": dealer.dealer_id,
        "loading_staff_id": loader.staff_id,
        "verified_by_id": verifier.staff_id,
        "design_id": design.design_id,
        "grade_id": grade.grade_id,
    }


def test_tc058_future_sales_date_raises_validation_error(db_session):
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    payload = SalesCreate(
        sales_date=date.today() + timedelta(days=1),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_sale(payload)
    assert "future" in exc.value.message.lower()


def test_tc059_sales_date_older_than_7_days_raises_validation_error(db_session):
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    payload = SalesCreate(
        sales_date=date.today() - timedelta(days=8),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_sale(payload)
    assert "7 days" in exc.value.message.lower()


def test_tc060_dealer_place_snapshotted_onto_sales_header(db_session):
    """DS-013 — header.place is the snapshot of dealer.place at save time."""
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    payload = SalesCreate(
        sales_date=date.today(),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=3
            )
        ],
    )
    result = svc.save_sale(payload)
    assert result.place == "Dindivanam"


def test_tc062_inactive_verified_by_raises_validation_error(db_session):
    """AC-030 — verified_by_id must reference an active staff."""
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    verifier = db_session.get(StaffModel, ids["verified_by_id"])
    verifier.is_active = False
    db_session.flush()
    payload = SalesCreate(
        sales_date=date.today(),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=2
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        svc.save_sale(payload)
    assert "inactive" in exc.value.message.lower()


def test_tc063_inactive_design_grade_pair_raises_validation_error(db_session):
    """AC-031 — (design, grade) must be in active design_grade_map."""
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    pair = (
        db_session.query(DesignGradeMapModel)
        .filter_by(design_id=ids["design_id"], grade_id=ids["grade_id"])
        .one()
    )
    pair.is_active = False
    db_session.flush()
    payload = SalesCreate(
        sales_date=date.today(),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=1
            )
        ],
    )
    with pytest.raises(ValidationError):
        svc.save_sale(payload)


def test_tc065_save_sale_writes_ledger_with_negative_delta(db_session):
    """AC-033 — ledger delta = −nos and running_balance = prior − nos."""
    svc = SalesService(db_session)
    ids = _seed_sales_world(db_session)
    # Seed a prior +20 inward via direct ledger row for setup
    from src.domain import stock as stock_mod
    stock_mod.apply_inward(
        db_session, ids["design_id"], ids["grade_id"], date.today(), 20, 999, 1
    )
    db_session.commit()
    payload = SalesCreate(
        sales_date=date.today(),
        dealer_id=ids["dealer_id"],
        loading_staff_id=ids["loading_staff_id"],
        verified_by_id=ids["verified_by_id"],
        lines=[
            SalesLineCreate(
                design_id=ids["design_id"], grade_id=ids["grade_id"], nos=5
            )
        ],
    )
    svc.save_sale(payload)
    # Latest ledger row for (design, grade) has delta=-5, running_balance=15
    latest = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=ids["design_id"], grade_id=ids["grade_id"])
        .order_by(
            StockLedgerModel.txn_date.desc(), StockLedgerModel.ledger_id.desc()
        )
        .first()
    )
    assert latest.delta == -5
    assert latest.running_balance == 15
    assert latest.source_type == "sale"
