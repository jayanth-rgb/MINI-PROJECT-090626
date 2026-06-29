# T-058 — `presentation/schemas/sales_report.py` — Consolidation + Transaction rows

**Module:** M-005 · **Depends on:** — (Group A)

## Context anchor
Group-A peer of T-057. Mirrors the same Pydantic v2 + `from_attributes=True` pattern. `TransactionRow.place` is a **denormalized snapshot** captured at sale time per **DS-013** — it is NOT joined live from `tbl_dealer_master`.

## Implementation logic

```python
# backend/src/presentation/schemas/sales_report.py
from datetime import date

from pydantic import BaseModel, ConfigDict


class ConsolidationRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    total_nos: int


class TransactionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sales_date: date
    dealer_id: int
    dealer_name: str
    place: str
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    nos: int


class SalesReportResponse(BaseModel):
    consolidation: list[ConsolidationRow]
    transactions: list[TransactionRow]
```

## Constraints
- `TransactionRow.place` is `str` (denormalized snapshot — DS-013); do not type it `str | None`.
- Field order matches the LLD's column order for predictable JSON layout.
- `SalesReportResponse` is the only top-level response model exported alongside the two row schemas.

## Do not touch
- Any other file in the repo.

## Success criteria
- **Manual**: `python -c "from src.presentation.schemas.sales_report import ConsolidationRow, TransactionRow, SalesReportResponse; SalesReportResponse(consolidation=[], transactions=[])"` succeeds.
- **Automated**: T-062 + T-065 integration tests (TC-133, TC-140) instantiate + JSON-serialize these models.
- **DoD**: 3 BaseModels with the exact LLD field set; nothing else exported.

## Checkout
> *"ConsolidationRow, TransactionRow, SalesReportResponse created. Ready for SalesReportService projection in T-062."*
