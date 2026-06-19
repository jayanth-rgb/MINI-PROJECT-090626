# T-007 — Pydantic Schemas

**Module:** M-001 · **Depends on:** none · **TC refs:** TC-002, TC-003, TC-009, TC-013, TC-021

## Implementation logic

```python
# backend/src/presentation/schemas/master.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class _OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Supplier ----------------------------------------------------------
class SupplierCreate(BaseModel):
    supplier_name: str = Field(min_length=1)
    place: str = Field(min_length=1)


class SupplierUpdate(BaseModel):
    supplier_name: str | None = Field(default=None, min_length=1)
    place: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class SupplierRead(_OrmModel):
    supplier_id: int
    supplier_name: str
    place: str
    is_active: bool
    created_at: datetime


# Staff -------------------------------------------------------------
class StaffCreate(BaseModel):
    staff_name: str = Field(min_length=1)


class StaffUpdate(BaseModel):
    staff_name: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class StaffRead(_OrmModel):
    staff_id: int
    staff_name: str
    is_active: bool
    created_at: datetime


# Dealer ------------------------------------------------------------
class DealerCreate(BaseModel):
    dealer_name: str = Field(min_length=1)
    place: str = Field(min_length=1)


class DealerUpdate(BaseModel):
    dealer_name: str | None = Field(default=None, min_length=1)
    place: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class DealerRead(_OrmModel):
    dealer_id: int
    dealer_name: str
    place: str
    is_active: bool
    created_at: datetime


# Grade (no created_at) ---------------------------------------------
class GradeCreate(BaseModel):
    grade_code: str = Field(min_length=1)  # strip in service if needed


class GradeUpdate(BaseModel):
    grade_code: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class GradeRead(_OrmModel):
    grade_id: int
    grade_code: str
    is_active: bool


# TradingDesign -----------------------------------------------------
class DesignCreate(BaseModel):
    size: str = Field(min_length=1)
    design_name: str = Field(min_length=1)


class DesignUpdate(BaseModel):
    size: str | None = Field(default=None, min_length=1)
    design_name: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class DesignRead(_OrmModel):
    design_id: int
    size: str
    design_name: str
    is_active: bool
    created_at: datetime


# DesignGradeMap (no created_at) ------------------------------------
class DesignGradeMapCreate(BaseModel):
    design_id: int = Field(gt=0)
    grade_id: int = Field(gt=0)


class DesignGradeMapUpdate(BaseModel):
    is_active: bool | None = None


class DesignGradeMapRead(_OrmModel):
    map_id: int
    design_id: int
    grade_id: int
    is_active: bool
    design_name: str | None = None
    grade_code: str | None = None


class DesignGradeReadMin(BaseModel):
    grade_id: int
    grade_code: str
```

## Constraints
- DS-007: presentation layer; no domain or infrastructure imports
- TC-002, TC-003, TC-009, TC-013, TC-021: enforce min_length=1 on the listed fields
- Grade + DesignGradeMap Read schemas have NO created_at (matches T-004 ORM)
- DesignGradeMapRead hydrates design_name + grade_code from joined relationships (LLD line 651-655)

## Do not touch
Any other file.

## Success criteria
- **Manual:** `python -c "from src.presentation.schemas.master import SupplierCreate; SupplierCreate(supplier_name='', place='X')"` raises `pydantic.ValidationError`
- **Automated:** TC-002, TC-003, TC-009, TC-013, TC-021 (implemented in T-impl phase)
- **DoD:** All exports per LLD interface; min_length enforced; Read uses from_attributes=True

## Checkout prompt
*"Pydantic schemas created for all 6 entities (Create/Update/Read) + DesignGradeReadMin. Validation TC-002/003/009/013/021 ready."*
