# T-080 — `infrastructure/db/repositories/pricing.py` — pricing repositories

**Module:** M-011 · **Wave:** 2 (after T-079) · **Depends on:** T-079 (pricing models)

## Context anchor

Three repositories for M-011 data access. DS-012: all extend BaseRepository[T]. DS-022: `get_active_price` implements effective-from ordering. `InvoiceRepository.create_with_lines` is the only place that constructs `InvoiceHeaderModel` + `InvoiceLineModel` rows — all in one flush (no partial commit).

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/pricing.py
from datetime import date as date_type
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models.pricing import (
    PriceMasterModel, InvoiceHeaderModel, InvoiceLineModel, PaymentModel
)
from infrastructure.db.repositories.base import BaseRepository


class PriceMasterRepository(BaseRepository[PriceMasterModel]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, PriceMasterModel)

    def get_active_price(self, design_id: int, grade_id: int) -> PriceMasterModel | None:
        today = date_type.today()
        stmt = (
            select(PriceMasterModel)
            .where(
                PriceMasterModel.design_id == design_id,
                PriceMasterModel.grade_id == grade_id,
                PriceMasterModel.is_active == True,
                PriceMasterModel.effective_from <= today,
            )
            .order_by(PriceMasterModel.effective_from.desc())
            .limit(1)
        )
        return self._db.scalar(stmt)

    def list_all(self) -> list[PriceMasterModel]:
        stmt = (
            select(PriceMasterModel)
            .order_by(
                PriceMasterModel.design_id,
                PriceMasterModel.grade_id,
                PriceMasterModel.effective_from.desc(),
            )
        )
        return list(self._db.scalars(stmt).all())


class InvoiceRepository(BaseRepository[InvoiceHeaderModel]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, InvoiceHeaderModel)

    def create_with_lines(
        self,
        header_data: dict,
        lines_data: list[dict],
    ) -> InvoiceHeaderModel:
        header = InvoiceHeaderModel(**header_data)
        self._db.add(header)
        self._db.flush()  # get header.id
        for line_dict in lines_data:
            line = InvoiceLineModel(invoice_header_id=header.id, **line_dict)
            self._db.add(line)
        self._db.flush()
        self._db.refresh(header)
        return header

    def get(self, invoice_id: int) -> InvoiceHeaderModel | None:
        stmt = (
            select(InvoiceHeaderModel)
            .options(
                joinedload(InvoiceHeaderModel.lines),
                joinedload(InvoiceHeaderModel.payments),
            )
            .where(InvoiceHeaderModel.id == invoice_id)
        )
        return self._db.scalar(stmt)

    def list(
        self,
        dealer_id: int | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        status: str | None = None,
    ) -> list[InvoiceHeaderModel]:
        from infrastructure.db.models.transactions import SalesHeaderModel
        stmt = select(InvoiceHeaderModel).join(
            SalesHeaderModel, InvoiceHeaderModel.sales_header_id == SalesHeaderModel.id
        )
        if dealer_id is not None:
            stmt = stmt.where(SalesHeaderModel.dealer_id == dealer_id)
        if date_from:
            stmt = stmt.where(InvoiceHeaderModel.invoice_date >= date_from)
        if date_to:
            stmt = stmt.where(InvoiceHeaderModel.invoice_date <= date_to)
        if status:
            stmt = stmt.where(InvoiceHeaderModel.status == status)
        stmt = stmt.order_by(InvoiceHeaderModel.invoice_date.desc())
        return list(self._db.scalars(stmt).all())


class PaymentRepository(BaseRepository[PaymentModel]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, PaymentModel)

    def create(self, invoice_header_id: int, data) -> PaymentModel:
        payment = PaymentModel(
            invoice_header_id=invoice_header_id,
            payment_date=data.payment_date,
            amount=data.amount,
            notes=data.notes,
        )
        self._db.add(payment)
        self._db.flush()
        return payment
```

## Constraints

- `PriceMasterRepository.get_active_price`: `effective_from <= today()` — uses Python `date.today()` for the cutoff (not SQL `NOW()`) so it's testable without mocking DB time functions.
- `InvoiceRepository.create_with_lines`: uses `flush()` not `commit()` — the InvoiceService controls commit/rollback at the service level.
- `InvoiceRepository.get` uses `joinedload` to eagerly load lines and payments — avoids N+1 in InvoiceRead serialization.
- `PaymentRepository.create` receives a `PaymentCreate` Pydantic schema — unpacks `.payment_date`, `.amount`, `.notes` explicitly (not `**data.model_dump()`) to stay explicit.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.infrastructure.db.repositories.pricing import PriceMasterRepository; print('ok')`
- **Automated**: TC-187 (get_active_price returns most recent effective_from), TC-188 (inactive price → None), TC-189 (create_with_lines returns header with lines loaded).
- **DoD**: 3 classes exported. All extend BaseRepository. `get_active_price` ORDER BY effective_from DESC LIMIT 1. `create_with_lines` atomic (single flush block).

## Checkout

> *"repositories/pricing.py created. 3 repositories: PriceMasterRepository (effective-from lookup), InvoiceRepository (atomic create_with_lines + joinedload get), PaymentRepository (simple create). TC-187..TC-189 covered."*
