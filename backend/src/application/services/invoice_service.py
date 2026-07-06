import logging
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.invoice import (
    compute_invoice_status,
    compute_invoice_total,
    compute_line_total,
    generate_invoice_number,
)
from src.infrastructure.db.models.master import GradeModel, TradingDesignModel
from src.infrastructure.db.models.pricing import InvoiceHeaderModel
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from src.infrastructure.db.repositories.pricing import (
    InvoiceRepository,
    PaymentRepository,
    PriceMasterRepository,
)
from src.presentation.schemas.pricing import (
    InvoiceLineRead,
    InvoiceRead,
    InvoiceSummary,
    PaymentCreate,
    PaymentRead,
)

logger = logging.getLogger(__name__)


class InvoiceService:

    def __init__(self, db: Session) -> None:
        self._db = db
        self._invoice_repo = InvoiceRepository(db)
        self._payment_repo = PaymentRepository(db)
        self._price_repo = PriceMasterRepository(db)

    def _to_invoice_read(self, invoice: InvoiceHeaderModel) -> InvoiceRead:
        design_ids = list({line.design_id for line in invoice.lines})
        grade_ids = list({line.grade_id for line in invoice.lines})

        design_rows = self._db.scalars(
            select(TradingDesignModel).where(TradingDesignModel.design_id.in_(design_ids))
        ).all()
        grade_rows = self._db.scalars(
            select(GradeModel).where(GradeModel.grade_id.in_(grade_ids))
        ).all()

        design_map = {d.design_id: d for d in design_rows}
        grade_map = {g.grade_id: g for g in grade_rows}

        line_reads = [
            InvoiceLineRead(
                id=line.id,
                sales_line_id=line.sales_line_id,
                design_id=line.design_id,
                design_name=design_map[line.design_id].design_name,
                size=design_map[line.design_id].size,
                grade_id=line.grade_id,
                grade_code=grade_map[line.grade_id].grade_code,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total,
            )
            for line in invoice.lines
        ]

        return InvoiceRead(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            sales_header_id=invoice.sales_header_id,
            invoice_date=invoice.invoice_date,
            total_amount=invoice.total_amount,
            status=invoice.status,
            lines=line_reads,
            payments=[PaymentRead.model_validate(p) for p in invoice.payments],
        )

    def create_from_sales(self, sales_header_id: int) -> InvoiceRead:
        header = self._db.get(SalesHeaderModel, sales_header_id)
        if header is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales header {sales_header_id} not found",
            )

        already_invoiced = self._db.scalar(
            select(InvoiceHeaderModel.id)
            .where(InvoiceHeaderModel.sales_header_id == sales_header_id)
            .limit(1)
        )
        if already_invoiced:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invoice already exists for sales header {sales_header_id}",
            )

        lines_stmt = select(SalesLineModel).where(
            SalesLineModel.header_id == sales_header_id
        ).order_by(SalesLineModel.line_id)
        sales_lines = list(self._db.scalars(lines_stmt))

        lines_data: list[dict] = []
        line_totals: list[Decimal] = []
        for sl in sales_lines:
            price_row = self._price_repo.get_active_price(sl.design_id, sl.grade_id)
            if price_row is None:
                logger.warning(
                    "Invoice line for design_id=%s grade_id=%s created with unit_price=0"
                    " — no active price found",
                    sl.design_id,
                    sl.grade_id,
                )
            unit_price = price_row.unit_price if price_row is not None else Decimal("0.00")
            line_total = compute_line_total(sl.nos, unit_price)
            line_totals.append(line_total)
            lines_data.append({
                "sales_line_id": sl.line_id,
                "design_id": sl.design_id,
                "grade_id": sl.grade_id,
                "quantity": sl.nos,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        today = date.today()
        total_amount = (
            compute_invoice_total(line_totals) if line_totals else Decimal("0.00")
        )
        invoice_number = generate_invoice_number(today, sales_header_id)

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
        return self._to_invoice_read(invoice)

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found",
            )
        return self._to_invoice_read(invoice)

    def record_payment(self, invoice_id: int, data: PaymentCreate) -> InvoiceRead:
        invoice = self._invoice_repo.get(invoice_id)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found",
            )
        already_paid = sum((p.amount for p in invoice.payments), Decimal("0"))
        if already_paid + data.amount > invoice.total_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Payment would exceed invoice total. "
                    f"Remaining: {invoice.total_amount - already_paid}"
                ),
            )
        self._payment_repo.create(invoice_id, data)
        all_paid = [p.amount for p in invoice.payments] + [data.amount]
        new_status = compute_invoice_status(invoice.total_amount, all_paid)
        invoice.status = new_status
        self._db.commit()
        self._db.refresh(invoice)
        return self._to_invoice_read(invoice)
