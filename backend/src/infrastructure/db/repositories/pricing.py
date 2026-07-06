from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.infrastructure.db.models.pricing import (
    InvoiceHeaderModel,
    InvoiceLineModel,
    PaymentModel,
    PriceMasterModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class PriceMasterRepository(BaseRepository[PriceMasterModel]):

    def get_active_price(self, design_id: int, grade_id: int) -> PriceMasterModel | None:
        today = date_type.today()
        stmt = (
            select(PriceMasterModel)
            .where(
                PriceMasterModel.design_id == design_id,
                PriceMasterModel.grade_id == grade_id,
                PriceMasterModel.is_active.is_(True),
                PriceMasterModel.effective_from <= today,
            )
            .order_by(PriceMasterModel.effective_from.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[PriceMasterModel]:
        stmt = (
            select(PriceMasterModel)
            .order_by(
                PriceMasterModel.design_id,
                PriceMasterModel.grade_id,
                PriceMasterModel.effective_from.desc(),
            )
        )
        return list(self.session.execute(stmt).scalars())


class InvoiceRepository(BaseRepository[InvoiceHeaderModel]):

    def create_with_lines(
        self,
        header_data: dict,
        lines_data: list[dict],
    ) -> InvoiceHeaderModel:
        header = InvoiceHeaderModel(**header_data)
        self.session.add(header)
        self.session.flush()
        for line_dict in lines_data:
            line = InvoiceLineModel(invoice_header_id=header.id, **line_dict)
            self.session.add(line)
        self.session.flush()
        return self.get(header.id)

    def get(self, invoice_id: int) -> InvoiceHeaderModel | None:
        stmt = (
            select(InvoiceHeaderModel)
            .options(
                joinedload(InvoiceHeaderModel.lines),
                joinedload(InvoiceHeaderModel.payments),
            )
            .where(InvoiceHeaderModel.id == invoice_id)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def list(
        self,
        dealer_id: int | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        status: str | None = None,
    ) -> list[InvoiceHeaderModel]:
        from src.infrastructure.db.models.transactions import SalesHeaderModel
        stmt = (
            select(InvoiceHeaderModel)
            .join(SalesHeaderModel, InvoiceHeaderModel.sales_header_id == SalesHeaderModel.header_id)
        )
        if dealer_id is not None:
            stmt = stmt.where(SalesHeaderModel.dealer_id == dealer_id)
        if date_from is not None:
            stmt = stmt.where(InvoiceHeaderModel.invoice_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(InvoiceHeaderModel.invoice_date <= date_to)
        if status is not None:
            stmt = stmt.where(InvoiceHeaderModel.status == status)
        stmt = stmt.order_by(InvoiceHeaderModel.invoice_date.desc())
        return list(self.session.execute(stmt).scalars())


class PaymentRepository(BaseRepository[PaymentModel]):

    def create(self, invoice_header_id: int, data) -> PaymentModel:
        payment = PaymentModel(
            invoice_header_id=invoice_header_id,
            payment_date=data.payment_date,
            amount=data.amount,
            notes=data.notes,
        )
        self.session.add(payment)
        self.session.flush()
        return payment
