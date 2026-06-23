"""TC-053, 064, 069, 088, 089 — DB-level CHECK + FK RESTRICT constraints (T-042 + T-044)."""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    AdjustmentHeaderModel,
    InwardHeaderModel,
    InwardLineModel,
    SalesHeaderModel,
    SalesLineModel,
    StockLedgerModel,
)


def test_tc053_inward_line_check_nos_positive_rejects_zero(db_session):
    """ck_inward_line_nos_positive: nos = 0 raises IntegrityError."""
    supplier = SupplierModel(supplier_name="X", place="Y")
    staff = StaffModel(staff_name="S")
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    db_session.add_all([supplier, staff, design, grade])
    db_session.flush()
    header = InwardHeaderModel(
        purchase_date=date.today(),
        supplier_id=supplier.supplier_id,
        place=supplier.place,
        entered_by_id=staff.staff_id,
    )
    db_session.add(header)
    db_session.flush()
    db_session.add(
        InwardLineModel(
            header_id=header.header_id,
            design_id=design.design_id,
            grade_id=grade.grade_id,
            nos=0,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tc064_sales_line_check_nos_positive_rejects_zero(db_session):
    """ck_sales_line_nos_positive: nos = 0 raises IntegrityError."""
    dealer = DealerModel(dealer_name="D", place="P")
    loader = StaffModel(staff_name="L")
    verifier = StaffModel(staff_name="V")
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    db_session.add_all([dealer, loader, verifier, design, grade])
    db_session.flush()
    header = SalesHeaderModel(
        sales_date=date.today(),
        dealer_id=dealer.dealer_id,
        place=dealer.place,
        loading_staff_id=loader.staff_id,
        verified_by_id=verifier.staff_id,
    )
    db_session.add(header)
    db_session.flush()
    db_session.add(
        SalesLineModel(
            header_id=header.header_id,
            design_id=design.design_id,
            grade_id=grade.grade_id,
            nos=0,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tc069_adjustment_header_check_stock_date_le_entry_date(db_session):
    """ck_adjustment_header_dates: stock_date > entry_date raises IntegrityError."""
    design = TradingDesignModel(size="16X10", design_name="D")
    staff = StaffModel(staff_name="S")
    db_session.add_all([design, staff])
    db_session.flush()
    db_session.add(
        AdjustmentHeaderModel(
            stock_date=date(2026, 6, 22),
            entry_date=date(2026, 6, 21),
            design_id=design.design_id,
            entered_by_id=staff.staff_id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tc088_stock_ledger_check_source_type_rejects_unknown(db_session):
    """ck_stock_ledger_source_type: source_type = 'foo' raises IntegrityError."""
    design = TradingDesignModel(size="16X10", design_name="D")
    grade = GradeModel(grade_code="1")
    db_session.add_all([design, grade])
    db_session.flush()
    db_session.add(
        StockLedgerModel(
            design_id=design.design_id,
            grade_id=grade.grade_id,
            txn_date=date.today(),
            source_type="foo",  # not in CHECK list
            delta=1,
            running_balance=1,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tc089_fk_restrict_blocks_hard_delete_of_supplier_with_inward_rows(db_session):
    """tbl_inward_header.supplier_id ON DELETE RESTRICT — hard DELETE raises."""
    supplier = SupplierModel(supplier_name="X", place="Y")
    staff = StaffModel(staff_name="S")
    db_session.add_all([supplier, staff])
    db_session.flush()
    header = InwardHeaderModel(
        purchase_date=date.today(),
        supplier_id=supplier.supplier_id,
        place=supplier.place,
        entered_by_id=staff.staff_id,
    )
    db_session.add(header)
    db_session.flush()
    db_session.delete(supplier)
    with pytest.raises(IntegrityError):
        db_session.flush()
