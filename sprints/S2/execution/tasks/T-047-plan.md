# T-047 — InwardService (F-007)

**Module:** M-002 · **Depends on:** T-043, T-045, T-046 · **DS:** DS-002, DS-007, DS-013

## Implementation logic

```python
# backend/src/application/services/inward_service.py
from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy.orm import Session

from src.application.services._common import today  # use a helper if it exists; else datetime.date.today()
from src.domain import stock
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.db.repositories.master import (
    SupplierRepository, StaffRepository, TradingDesignRepository, GradeRepository,
    DesignGradeMapRepository,
)
from src.infrastructure.db.repositories.transactions import InwardHeaderRepository
from src.presentation.schemas.master import SupplierRead  # for hydration
from src.presentation.schemas.transactions import InwardCreate, InwardRead

MAX_BACKDATE_DAYS = 7


class InwardService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = InwardHeaderRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.staff_repo = StaffRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.grade_repo = GradeRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def save_inward(self, payload: InwardCreate) -> InwardRead:
        today_ = date.today()
        # AC-020 / AC-021
        if payload.purchase_date > today_:
            raise ValidationError("purchase_date cannot be in the future")
        if payload.purchase_date < today_ - timedelta(days=MAX_BACKDATE_DAYS):
            raise ValidationError(f"purchase_date cannot be older than {MAX_BACKDATE_DAYS} days")

        # AC-022 / DS-013 — supplier exists+active; snapshot place
        try:
            supplier = self.supplier_repo.get(payload.supplier_id)
        except NotFoundError:
            raise NotFoundError("Supplier", payload.supplier_id)
        if not supplier.is_active:
            raise ValidationError(f"Supplier {payload.supplier_id} is inactive")

        # Staff active check
        try:
            staff = self.staff_repo.get(payload.entered_by_id)
        except NotFoundError:
            raise NotFoundError("Staff", payload.entered_by_id)
        if not staff.is_active:
            raise ValidationError(f"Staff {payload.entered_by_id} is inactive")

        # AC-025 strip; AC-024 nos > 0 enforced post-strip
        kept_lines = [l for l in payload.lines if l.nos is not None and l.nos > 0]
        # AC-026
        if not kept_lines:
            raise ValidationError("at least one line with nos > 0 required")

        # AC-023 — each line's (design, grade) must be in active design_grade_map
        for line in kept_lines:
            # Validate design + grade exist + active
            d = self.design_repo.get(line.design_id)
            if not d.is_active:
                raise ValidationError(f"Design {line.design_id} is inactive")
            g = self.grade_repo.get(line.grade_id)
            if not g.is_active:
                raise ValidationError(f"Grade {line.grade_id} is inactive")
            pair = self.map_repo.get_by_pair(line.design_id, line.grade_id)
            if pair is None or not pair.is_active:
                raise ValidationError(
                    f"(design_id, grade_id) = ({line.design_id}, {line.grade_id}) is not an active mapping"
                )

        # Persist header + lines
        header = self.repo.create_with_lines(
            header_payload={
                "purchase_date": payload.purchase_date,
                "supplier_id": payload.supplier_id,
                "place": supplier.place,  # DS-013 snapshot
                "entered_by_id": payload.entered_by_id,
            },
            line_payloads=[
                {"design_id": l.design_id, "grade_id": l.grade_id, "nos": l.nos}
                for l in kept_lines
            ],
        )

        # Apply ledger writes
        for line in header.lines:
            stock.apply_inward(
                self.session, line.design_id, line.grade_id, payload.purchase_date,
                line.nos, header.header_id, line.line_id,
            )

        self.session.commit()
        # Reload for hydrated Read (cascade='all, delete-orphan' on lines + lazy=joined)
        return InwardRead.model_validate(header)

    def list_inwards(self, date_from: date | None = None, date_to: date | None = None) -> list[InwardRead]:
        # Simple repo.list with optional date filter (extend BaseRepository or inline a select())
        ...
```

## Constraints
- DS-002: `stock.apply_inward` does the locking — the service must invoke it INSIDE the same session.
- DS-007: validate → persist → apply ledger → commit, in that order. No skipping the order.
- DS-013: `place = supplier.place` snapshot; never lookup at read time.
- AC-022/030: master must be `is_active` at save time (otherwise reject with ValidationError, not silent).
- The 7-day backdate cap lives in the service (AC-021), NOT in `domain.stock` (kept pure).

## Do not touch
Any other file.

## Success criteria
- **Manual:** save a valid payload; header + lines present; ledger has one row per line.
- **Automated:** TC-047, TC-049, TC-050, TC-051, TC-054, TC-055, TC-056 all pass.
- **DoD:** All AC-020..AC-027 invariants enforced in this service method.

## Checkout prompt
*"InwardService created; atomic save with ledger updates per line."*
