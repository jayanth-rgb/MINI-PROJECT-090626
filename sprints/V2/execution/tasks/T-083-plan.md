# T-083 — `services/pricing_service.py` — PricingService

**Module:** M-011 · **Wave:** 3 (after T-079, T-080, T-082) · **Depends on:** T-079, T-080, T-082

## Context anchor

Price Master CRUD. DS-008: soft-delete (is_active=false) — no hard delete. DS-022: PricingService does NOT compute invoices — that's InvoiceService. Uniqueness check done via SELECT (not IntegrityError catch) to produce clean 409 with informative message. Validation of design_id and grade_id existence prevents foreign key errors at DB level.

## Implementation logic

```python
# backend/src/application/services/pricing_service.py
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models.master import TradingDesignModel, GradeModel
from infrastructure.db.models.pricing import PriceMasterModel
from infrastructure.db.repositories.pricing import PriceMasterRepository
from presentation.schemas.pricing import PriceMasterCreate, PriceMasterUpdate


class PricingService:

    def __init__(self, db: Session) -> None:
        self._repo = PriceMasterRepository(db)
        self._db = db

    def list_prices(self) -> list[PriceMasterModel]:
        return self._repo.list_all()

    def create_price(self, data: PriceMasterCreate) -> PriceMasterModel:
        # Validate design_id exists
        design = self._db.get(TradingDesignModel, data.design_id)
        if design is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Design {data.design_id} not found")
        # Validate grade_id exists
        grade = self._db.get(GradeModel, data.grade_id)
        if grade is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Grade {data.grade_id} not found")
        # Uniqueness check before insert
        existing = self._db.scalar(
            select(PriceMasterModel).where(
                PriceMasterModel.design_id == data.design_id,
                PriceMasterModel.grade_id == data.grade_id,
                PriceMasterModel.effective_from == data.effective_from,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Price already exists for design={data.design_id}, grade={data.grade_id}, effective_from={data.effective_from}",
            )
        price = PriceMasterModel(
            design_id=data.design_id,
            grade_id=data.grade_id,
            unit_price=data.unit_price,
            effective_from=data.effective_from,
            is_active=True,
        )
        return self._repo.create(price)

    def update_price(self, price_id: int, data: PriceMasterUpdate) -> PriceMasterModel:
        price = self._repo.get(price_id)
        if price is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Price {price_id} not found")
        if data.unit_price is not None:
            price.unit_price = data.unit_price
        if data.is_active is not None:
            price.is_active = data.is_active
        return self._repo.update(price)
```

## Constraints

- `create_price` performs a `SELECT` before `INSERT` — this avoids catching `IntegrityError` from the DB which is harder to differentiate from other constraint violations.
- `create_price` validates design + grade existence via `db.get()` — raises 404 before attempting insert if either FK is invalid.
- `update_price` only updates explicitly-provided fields (`data.unit_price is not None`) — partial PATCH semantics.
- No `delete_price` method — DS-008 soft-delete via `update_price(is_active=False)`.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.application.services.pricing_service import PricingService; print(dir(PricingService))` includes list_prices, create_price, update_price.
- **Automated**: TC-201 (dup price → 409).
- **DoD**: 3 methods. create_price SELECT-before-INSERT. update_price partial-patch safe. No hard delete.

## Checkout

> *"PricingService created. list_prices + create_price (409 via pre-insert SELECT) + update_price (partial patch). TC-201 covered."*
