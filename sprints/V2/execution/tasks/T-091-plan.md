# T-091 — `routers/invoices.py` — Invoice CRUD + Payment Recording

**Module:** M-011 · **Wave:** 5 (after T-089) · **Depends on:** T-084, T-089

## Context anchor

On-demand invoicing (DS-023): invoices are NEVER auto-triggered. Only SUPERVISOR can create via `POST /invoices?sales_header_id={id}` (query param, not body). `UNIQUE(sales_header_id)` on `tbl_invoice_header` ensures one invoice per sales order — InvoiceService raises 409 on duplicate. Payment recording also SUPERVISOR-only. GET endpoints are available to all authenticated roles.

## Implementation logic

```python
# backend/src/presentation/api/routers/invoices.py
from fastapi import APIRouter, Depends, Query, status

from presentation.api.dependencies import get_invoice_service, get_current_user, require_supervisor
from application.services.invoice_service import InvoiceService
from presentation.schemas.pricing import InvoiceRead, InvoiceSummary, PaymentCreate
from infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceSummary])
def list_invoices(
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(get_current_user),
):
    return svc.list_invoices()


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(
    sales_header_id: int = Query(...),
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.create_from_sales(sales_header_id)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(get_current_user),
):
    return svc.get_invoice(invoice_id)


@router.post("/{invoice_id}/payments", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def record_payment(
    invoice_id: int,
    payload: PaymentCreate,
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.record_payment(invoice_id, payload.amount)
```

## Constraints

- `sales_header_id` is a **query param** (`Query(...)`) on POST — call as `POST /invoices?sales_header_id=42`.
- `InvoiceSummary` for list (lightweight, no nested lines/payments). `InvoiceRead` for detail + create + payment responses (nested).
- `PaymentCreate.amount` is `Decimal` with `gt=0` (validated at schema level, T-082) — no additional validation needed in router.
- 409 on duplicate invoice (UNIQUE constraint) raised by InvoiceService (T-084).
- 422 on overpayment raised by InvoiceService (T-084).
- `record_payment` returns the UPDATED `InvoiceRead` (with new payment + recalculated status).

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.invoices import router; print(len(router.routes))"` → `4`
- **Automated**: TC-217
- **DoD**: 4 routes. GET endpoints any-auth. POST/payment SUPERVISOR-only. sales_header_id as Query param. InvoiceService wired.

## Checkout

> *"routers/invoices.py created. 4 endpoints: list, create (sales_header_id Query param per DS-023), get detail, record-payment. SUPERVISOR gate on create+payment. InvoiceRead with nested lines+payments returned. TC-217 covered."*
