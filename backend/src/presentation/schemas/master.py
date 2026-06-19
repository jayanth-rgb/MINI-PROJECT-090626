from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _OrmModel(BaseModel):
    """Base for Read schemas — enables ORM attribute access."""

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------- Supplier
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


# -------------------------------------------------------------------- Staff
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


# ------------------------------------------------------------------- Dealer
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


# -------------------------------------------------------- Grade (no created_at)
class GradeCreate(BaseModel):
    grade_code: str = Field(min_length=1)


class GradeUpdate(BaseModel):
    grade_code: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class GradeRead(_OrmModel):
    grade_id: int
    grade_code: str
    is_active: bool


# ------------------------------------------------------------- TradingDesign
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


# -------------------------------------------- DesignGradeMap (no created_at)
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


# ---------------------------- Minimal projection for AC-019 / DF-006 contract
class DesignGradeReadMin(BaseModel):
    grade_id: int
    grade_code: str
