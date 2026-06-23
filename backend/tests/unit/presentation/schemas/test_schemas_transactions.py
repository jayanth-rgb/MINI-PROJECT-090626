"""TC-052, 061, 067, 068, 072, 073 — T-046 Pydantic schemas (transactions)."""
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.presentation.schemas.transactions import (
    AdjustmentCreate,
    AdjustmentLineCreate,
    InwardLineCreate,
    SalesCreate,
    SalesLineCreate,
)


def test_tc052_inward_line_create_rejects_negative_nos():
    with pytest.raises(PydanticValidationError):
        InwardLineCreate(design_id=1, grade_id=1, nos=-1)


def test_tc061_sales_create_rejects_payload_missing_loading_staff_id():
    """Both loading_staff_id and verified_by_id are required (AC-030)."""
    with pytest.raises(PydanticValidationError):
        SalesCreate(
            sales_date=date.today(),
            dealer_id=1,
            verified_by_id=1,
            # loading_staff_id intentionally missing
            lines=[SalesLineCreate(design_id=1, grade_id=1, nos=1)],
        )  # type: ignore[call-arg]


def test_tc067_adjustment_create_design_id_lives_on_header_not_line():
    """AC-034 — design_id is a HEADER field only. Verify the schema's field set
    so a future regression that accidentally adds design_id to the line schema
    is caught (Pydantic v2 defaults to extra='ignore' so extra args don't raise)."""
    from src.presentation.schemas.transactions import AdjustmentCreate
    line_fields = set(AdjustmentLineCreate.model_fields.keys())
    header_fields = set(AdjustmentCreate.model_fields.keys())
    assert "design_id" not in line_fields, (
        f"AC-034 violated: design_id leaked onto AdjustmentLineCreate: {line_fields}"
    )
    assert "design_id" in header_fields, (
        f"AC-034 violated: design_id missing from AdjustmentCreate header: {header_fields}"
    )


def test_tc068_adjustment_create_rejects_stock_date_after_entry_date():
    with pytest.raises(PydanticValidationError) as exc:
        AdjustmentCreate(
            stock_date=date(2026, 6, 22),
            entry_date=date(2026, 6, 21),
            design_id=1,
            entered_by_id=1,
            lines=[AdjustmentLineCreate(grade_id=1, physical_cb=10)],
        )
    assert "on or before" in str(exc.value).lower() or "stock_date" in str(exc.value).lower()


def test_tc072_adjustment_line_create_rejects_negative_physical_cb():
    with pytest.raises(PydanticValidationError):
        AdjustmentLineCreate(grade_id=1, physical_cb=-1)


def test_tc073_adjustment_line_create_accepts_zero_physical_cb():
    """AC-037 — physical_cb=0 is valid (zero stock count is a valid measurement)."""
    line = AdjustmentLineCreate(grade_id=1, physical_cb=0)
    assert line.physical_cb == 0
