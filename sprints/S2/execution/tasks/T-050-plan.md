# T-050 — DesignGradeCbService (DF-003 / AC-036)

**Module:** M-002 · **Depends on:** T-045, T-046 · **DS:** DS-007

## Implementation logic

```python
# backend/src/application/services/design_grade_cb_service.py
from datetime import date
from sqlalchemy.orm import Session

from src.domain import stock
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.db.repositories.master import (
    TradingDesignRepository, DesignGradeMapRepository,
)
from src.presentation.schemas.transactions import DesignGradeReadWithCb


class DesignGradeCbService:
    def __init__(self, session: Session):
        self.session = session
        self.design_repo = TradingDesignRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def list_active_grades_with_cb(
        self, design_id: int, stock_date: date
    ) -> list[DesignGradeReadWithCb]:
        design = self.design_repo.get(design_id)
        if not design.is_active:
            raise NotFoundError("TradingDesign", design_id)

        rows = self.map_repo.list_active_by_design(design_id)  # JOIN filter on grade.is_active too
        return [
            DesignGradeReadWithCb(
                grade_id=r.grade_id,
                grade_code=r.grade.grade_code,
                software_cb=stock.closing_balance(self.session, design_id, r.grade_id, stock_date),
            )
            for r in rows
        ]
```

## Constraints
- AC-036: software_cb = `closing_balance(design, grade, stock_date)`. Computed at request time, not snapshotted.
- AC-040: If `rows` is empty (no active grades), service returns `[]`. The router does NOT convert empty list to 422 — empty array is the contract. The Adjustment form (frontend) treats `[]` as the ERR-012 trigger.
- DS-007: service-layer only. No HTTP.

## Do not touch
Any other file.

## Success criteria
- **Manual:** Call with seeded ledger; returns rows with software_cb.
- **Automated:** TC-070 passes.
- **DoD:** Active design + active grades filter applied; software_cb is closing_balance result.

## Checkout prompt
*"DesignGradeCbService created; DF-003 service-layer ready."*
