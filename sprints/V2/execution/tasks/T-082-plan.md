# T-082 — `presentation/schemas/pricing.py` — Pydantic v2 pricing + invoice schemas

**Module:** M-011 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Pure Pydantic file. 8 schemas for M-011 (Pricing & Invoicing). DS-022: `InvoiceLineRead.unit_price` is a point-in-time snapshot — not a FK reference. DS-023: `InvoiceSummary` is header-only (no lines) for use in list endpoints.

## Implementation logic

```python
# backend/src/presentation/schemas/pricing.py
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
```

## Constraints

- `PriceMasterCreate.unit_price` Field(ge=0) — zero is valid (DS-022 allows zero-price lines with warning).
- `PaymentCreate.amount` Field(gt=0) — payments must be positive.
- `InvoiceLineRead.design_name`, `.size`, `.grade_code` are denormalized fields — populated by InvoiceService at creation time (no lazy join needed on InvoiceLineModel because these aren't stored on the ORM; they'll be set explicitly when building InvoiceRead).
- `InvoiceRead` has nested `lines` and `payments` — `from_attributes=True` allows SQLAlchemy relationship lazy-loading to populate them.
- `InvoiceSummary` has no `lines`/`payments` — used only in list endpoints for performance.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.presentation.schemas.pricing import InvoiceRead; len(InvoiceRead.model_fields)` → 8
- **Automated**: TC-202..TC-206 (InvoiceService tests) serialize InvoiceRead from DB results.
- **DoD**: 8 schemas exported. PaymentCreate amount gt=0. PriceMasterCreate unit_price ge=0. InvoiceRead/InvoiceLineRead/PaymentRead/PriceMasterRead/InvoiceSummary all have from_attributes=True. No project imports beyond pydantic.

## Checkout

> *"schemas/pricing.py created. 8 Pydantic v2 schemas for pricing and invoicing. Ready for T-083 (PricingService) and T-084 (InvoiceService)."*
