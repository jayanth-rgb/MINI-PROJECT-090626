from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────────────────────────
# Inward (F-007)
# ──────────────────────────────────────────────────────────────────────────────


class InwardLineCreate(BaseModel):
    design_id: int = Field(gt=0)
    grade_id: int = Field(gt=0)
    # RULE-017: None or 0 means "skip this row"; service strips before validating nos > 0.
    nos: Optional[int] = Field(default=None, ge=0)


class InwardCreate(BaseModel):
    purchase_date: date
    supplier_id: int = Field(gt=0)
    entered_by_id: int = Field(gt=0)
    lines: List[InwardLineCreate] = Field(min_length=1)
    # DS-013: `place` is server-derived from supplier at save; not user-editable.


class InwardLineRead(_OrmModel):
    line_id: int
    design_id: int
    grade_id: int
    nos: int


class InwardRead(_OrmModel):
    header_id: int
    purchase_date: date
    supplier_id: int
    place: str
    entered_by_id: int
    created_at: datetime
    lines: List[InwardLineRead] = []


# ──────────────────────────────────────────────────────────────────────────────
# Sales (F-008)
# ──────────────────────────────────────────────────────────────────────────────


class SalesLineCreate(BaseModel):
    design_id: int = Field(gt=0)
    grade_id: int = Field(gt=0)
    nos: Optional[int] = Field(default=None, ge=0)


class SalesCreate(BaseModel):
    sales_date: date
    dealer_id: int = Field(gt=0)
    loading_staff_id: int = Field(gt=0)
    verified_by_id: int = Field(gt=0)
    lines: List[SalesLineCreate] = Field(min_length=1)
    # DS-013: `place` is server-derived from dealer at save.


class SalesLineRead(_OrmModel):
    line_id: int
    design_id: int
    grade_id: int
    nos: int


class SalesRead(_OrmModel):
    header_id: int
    sales_date: date
    dealer_id: int
    place: str
    loading_staff_id: int
    verified_by_id: int
    created_at: datetime
    lines: List[SalesLineRead] = []


# ──────────────────────────────────────────────────────────────────────────────
# Adjustment (F-009) — single-design header per AC-034
# ──────────────────────────────────────────────────────────────────────────────


class AdjustmentLineCreate(BaseModel):
    grade_id: int = Field(gt=0)
    # AC-037: zero is valid (the user counted nothing in that grade-bin).
    physical_cb: int = Field(ge=0)
    # AC-036: software_cb is NOT in the request — service snapshots from ledger.


class AdjustmentCreate(BaseModel):
    stock_date: date
    entry_date: date
    design_id: int = Field(gt=0)
    entered_by_id: int = Field(gt=0)
    lines: List[AdjustmentLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dates(self) -> "AdjustmentCreate":
        # AC-035 (ERR-010): backstops the DB CHECK constraint at the API boundary.
        if self.stock_date > self.entry_date:
            raise ValueError("stock_date must be on or before entry_date")
        return self


class AdjustmentLineRead(_OrmModel):
    line_id: int
    grade_id: int
    software_cb: int
    physical_cb: int
    difference: int


class AdjustmentRead(_OrmModel):
    header_id: int
    stock_date: date
    entry_date: date
    design_id: int
    entered_by_id: int
    created_at: datetime
    lines: List[AdjustmentLineRead] = []


# ──────────────────────────────────────────────────────────────────────────────
# DF-003 contract — GET /designs/{id}/grades-with-cb response item
# ──────────────────────────────────────────────────────────────────────────────


class DesignGradeReadWithCb(BaseModel):
    grade_id: int
    grade_code: str
    software_cb: int
