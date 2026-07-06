"""Invoice CRUD and payment recording router.

Endpoints
---------
GET  /invoices                      — list invoices (any authenticated user)
POST /invoices?sales_header_id=N    — create invoice from a sales order (SUPERVISOR only)
GET  /invoices/{invoice_id}         — full invoice detail with lines + payments (any auth)
POST /invoices/{invoice_id}/payments— record a payment against an invoice (SUPERVISOR only)

DS-023: Invoicing is on-demand only — no auto-trigger logic.
DS-019: SUPERVISOR-only enforcement via Depends(require_supervisor) on write endpoints.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status

from src.application.services.invoice_service import InvoiceService
from src.infrastructure.db.models.auth import UserModel
from src.presentation.api.dependencies import (
    get_current_user,
    get_invoice_service,
    require_supervisor,
)
from src.presentation.schemas.pricing import InvoiceRead, InvoiceSummary, PaymentCreate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceSummary])
def list_invoices(
    dealer_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(PENDING|PARTIAL|PAID)$"),
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(get_current_user),
) -> list[InvoiceSummary]:
    """List invoices with optional filters. Available to any authenticated user."""
    return svc.list_invoices(
        dealer_id=dealer_id,
        date_from=date_from,
        date_to=date_to,
        status_filter=status,
    )


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(
    sales_header_id: int = Query(...),
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(require_supervisor),
) -> InvoiceRead:
    """Create an invoice from a sales order. SUPERVISOR only.

    sales_header_id is a query parameter (DS-023 on-demand pattern).
    Returns 201 with the created InvoiceRead.
    Raises 404 if the sales order does not exist.
    Raises 409 if an invoice already exists for this sales order (UNIQUE constraint).
    """
    return svc.create_from_sales(sales_header_id)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(get_current_user),
) -> InvoiceRead:
    """Retrieve full invoice detail including nested lines and payments.

    Available to any authenticated user.
    Raises 404 if the invoice does not exist.
    """
    return svc.get_invoice(invoice_id)


@router.post(
    "/{invoice_id}/payments",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
def record_payment(
    invoice_id: int,
    payload: PaymentCreate,
    svc: InvoiceService = Depends(get_invoice_service),
    _: UserModel = Depends(require_supervisor),
) -> InvoiceRead:
    """Record a payment against an invoice. SUPERVISOR only.

    Returns the updated InvoiceRead with the new payment and recalculated status.
    Raises 404 if the invoice does not exist.
    Raises 422 if the payment would exceed the invoice total (overpayment guard).
    PaymentCreate.amount is validated gt=0 at the schema level (T-082).
    """
    return svc.record_payment(invoice_id, payload)
