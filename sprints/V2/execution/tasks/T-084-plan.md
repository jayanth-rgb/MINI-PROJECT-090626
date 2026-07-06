# T-084 — `services/invoice_service.py` — InvoiceService

**Module:** M-011 · **Wave:** 3 (after T-079, T-080, T-081, T-082) · **Depends on:** T-079, T-080, T-081, T-082

## Context anchor

The most complex service in V2. DS-022: unit_price snapshotted at creation (not FK reference). DS-023: one invoice per sale (UNIQUE constraint on sales_header_id), on-demand creation. `create_from_sales` is the only write path — reads from S2 repositories (TransactionRepository) and writes via InvoiceRepository.

## Implementation logic

```python
# backend/src/application/services/invoice_service.py
from datetime import date
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.invoice import (
    compute_line_total, compute_invoice_total,
    compute_invoice_status, generate_invoice_number,
)
from infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from infrastructure.db.repositories.pricing import (
    InvoiceRepository, PaymentRepository, PriceMasterRepository
)
from presentation.schemas.pricing import (
    InvoiceRead, InvoiceSummary, PaymentCreate
)


class InvoiceService:

    def __init__(self, db: Session) -> None:
        self._db = db
        self._invoice_repo = InvoiceRepository(db)
        self._payment_repo = PaymentRepository(db)
        self._price_repo = PriceMasterRepository(db)

    def create_from_sales(self, sales_header_id: int) -> InvoiceRead:
        # Step 1: Verify sales_header exists
        header = self._db.get(SalesHeaderModel, sales_header_id)
        if header is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Sales header {sales_header_id} not found")

        # Step 2: Check no prior invoice
        existing_invoices = self._invoice_repo.list(dealer_id=None)
        for inv in existing_invoices:
            if inv.sales_header_id == sales_header_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f"Invoice already exists for sales header {sales_header_id}")

        # Step 3: Fetch all sales_line rows
        lines_stmt = select(SalesLineModel).where(SalesLineModel.sales_header_id == sales_header_id)
        sales_lines = list(self._db.scalars(lines_stmt).all())

        # Step 4: Compute line totals with price snapshot
        lines_data = []
        line_totals = []
        for sl in sales_lines:
            price_row = self._price_repo.get_active_price(sl.design_id, sl.grade_id)
            unit_price = price_row.unit_price if price_row is not None else Decimal("0.00")
            notes = None if price_row is not None else "WARNING: No active price — unit_price=0"
            line_total = compute_line_total(sl.nos, unit_price)
            line_totals.append(line_total)
            lines_data.append({
                "sales_line_id": sl.id,
                "design_id": sl.design_id,
                "grade_id": sl.grade_id,
                "quantity": sl.nos,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        # Step 5+6: Compute totals
        total_amount = compute_invoice_total(line_totals) if line_totals else Decimal("0.00")
        today = date.today()
        invoice_number = generate_invoice_number(today, sales_header_id)

        # Step 7: Create invoice header + lines atomically
        header_data = {
            "invoice_number": invoice_number,
            "sales_header_id": sales_header_id,
            "invoice_date": today,
            "total_amount": total_amount,
            "status": "PENDING",
        }
        invoice = self._invoice_repo.create_with_lines(header_data, lines_data)
        self._db.commit()
        self._db.refresh(invoice)
        return InvoiceRead.model_validate(invoice)

    def list_invoices(
        self,
        dealer_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status_filter: str | None = None,
    ) -> list[InvoiceSummary]:
        invoices = self._invoice_repo.list(dealer_id, date_from, date_to, status_filter)
        return [InvoiceSummary.model_validate(inv) for inv in invoices]

    def get_invoice(self, invoice_id: int) -> InvoiceRead:
        invoice = self._invoice_repo.get(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Invoice {invoice_id} not found")
        return InvoiceRead.model_validate(invoice)

    def record_payment(self, invoice_id: int, data: PaymentCreate) -> InvoiceRead:
        invoice = self._invoice_repo.get(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Invoice {invoice_id} not found")
        # Overpayment guard
        already_paid = sum(p.amount for p in invoice.payments)
        if already_paid + data.amount > invoice.total_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Payment would exceed invoice total. Remaining: {invoice.total_amount - already_paid}",
            )
        self._payment_repo.create(invoice_id, data)
        # Recompute status
        all_paid = [p.amount for p in invoice.payments] + [data.amount]
        new_status = compute_invoice_status(invoice.total_amount, all_paid)
        invoice.status = new_status
        self._db.commit()
        self._db.refresh(invoice)
        return InvoiceRead.model_validate(invoice)
```

## Constraints

- `create_from_sales` checks for existing invoice with a Python-level loop (not DB UNIQUE — the DB constraint is the enforcement; this pre-check gives a clean 409 with message).
- `compute_invoice_total` raises `ValueError` if `line_totals` is empty — guard with `if line_totals` before calling; return `Decimal("0.00")` for zero-line sales (edge case).
- `unit_price` snapshotted from `get_active_price` at creation time — not from a FK (DS-022). Changes to price master after invoice creation have zero effect.
- `record_payment` refreshes `invoice` after commit so the returned `InvoiceRead` includes the new payment.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.application.services.invoice_service import InvoiceService; print('ok')`
- **Automated**: TC-202..TC-206.
- **DoD**: 4 methods. create_from_sales uses generate_invoice_number + compute_ functions. Price snapshotted. record_payment recomputes status via compute_invoice_status. Overpayment → 422.

## Checkout

> *"InvoiceService created. create_from_sales (price snapshot + domain functions), list_invoices, get_invoice, record_payment (overpayment guard + status recompute). TC-202..TC-206 covered."*
