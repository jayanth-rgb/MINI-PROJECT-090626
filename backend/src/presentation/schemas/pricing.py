from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PriceMasterCreate(BaseModel):
    design_id: int
    grade_id: int
    unit_price: Decimal = Field(ge=0)
    effective_from: date


class PriceMasterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    unit_price: Decimal
    effective_from: date
    is_active: bool


class PriceMasterUpdate(BaseModel):
    unit_price: Decimal | None = None
    is_active: bool | None = None


class InvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sales_line_id: int
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_date: date
    amount: Decimal
    notes: str | None


class PaymentCreate(BaseModel):
    payment_date: date
    amount: Decimal = Field(gt=0)
    notes: str | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_number: str
    sales_header_id: int
    invoice_date: date
    total_amount: Decimal
    status: str
    lines: list[InvoiceLineRead]
    payments: list[PaymentRead]


class InvoiceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    status: str
    sales_header_id: int
