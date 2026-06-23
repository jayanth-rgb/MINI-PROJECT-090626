# T-046 — Pydantic v2 schemas for transactions

**Module:** M-002 · **Depends on:** — (standalone) · **DS:** DS-010, DS-013

## Implementation logic

```python
# backend/src/presentation/schemas/transactions.py
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ===== Inward =====
class InwardLineCreate(BaseModel):
    design_id: int = Field(gt=0)
    grade_id: int = Field(gt=0)
    nos: Optional[int] = Field(default=None, ge=0)  # None or 0 = skip (RULE-017)


class InwardCreate(BaseModel):
    purchase_date: date
    supplier_id: int = Field(gt=0)
    entered_by_id: int = Field(gt=0)
    lines: List[InwardLineCreate] = Field(min_length=1)
    # place NOT in request — server derives from supplier (DS-013)


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


# ===== Sales (mirror with dealer + 2 staff fields) =====
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


# ===== Adjustment (single-design header per AC-034) =====
class AdjustmentLineCreate(BaseModel):
    grade_id: int = Field(gt=0)
    physical_cb: int = Field(ge=0)  # 0 valid per AC-037


class AdjustmentCreate(BaseModel):
    stock_date: date
    entry_date: date
    design_id: int = Field(gt=0)
    entered_by_id: int = Field(gt=0)
    lines: List[AdjustmentLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dates(self) -> "AdjustmentCreate":
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


# ===== DF-003 contract =====
class DesignGradeReadWithCb(BaseModel):
    grade_id: int
    grade_code: str
    software_cb: int
```

## Constraints
- DS-013: `place` is NOT in any Create schema; service derives from master.
- AC-034: AdjustmentCreate has `design_id` on the header; AdjustmentLineCreate does NOT.
- AC-037: physical_cb `ge=0`, NOT `gt=0` — zero is valid.
- AC-035: cross-field validator on AdjustmentCreate using `@model_validator(mode="after")`.
- nos default `None` and `ge=0` allows None/0 → service strips per RULE-017.
- Read schemas use `_OrmModel` for `from_attributes=True`.

## Do not touch
Any other file.

## Success criteria
- **Manual:** Import all 13 schemas; instantiate AdjustmentCreate with stock_date > entry_date → ValidationError.
- **Automated:** TC-052, TC-061, TC-067, TC-068, TC-072, TC-073 all pass.
- **DoD:** 13 schemas; place absent from Create; physical_cb ≥ 0; stock_date ≤ entry_date validator.

## Checkout prompt
*"13 Pydantic schemas created; stock_date<=entry_date validator enforced."*
