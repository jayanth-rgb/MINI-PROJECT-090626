# T-076 — `presentation/schemas/inward_report.py` — Pydantic v2 inward report schemas

**Module:** M-009 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Pure Pydantic file. Mirrors `schemas/sales_report.py` (S3 T-058) exactly but for inward data. Three schemas consumed by T-077 (InwardReportService) and T-078 (inward_report router). DS-013: `place` on InwardTransactionRow is a `str` snapshot from `tbl_inward_header.place` — no re-join to supplier master.

## Implementation logic

```python
# backend/src/presentation/schemas/inward_report.py
from datetime import date
from pydantic import BaseModel, ConfigDict


class InwardConsolidationRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    total_nos: int


class InwardTransactionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purchase_date: date
    supplier_id: int
    supplier_name: str
    place: str          # DS-013: snapshot from tbl_inward_header.place
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    nos: int


class InwardReportResponse(BaseModel):
    consolidation: list[InwardConsolidationRow]
    transactions: list[InwardTransactionRow]
```

## Constraints

- `place` is `str` (not an Enum or FK) — matches DS-013 denormalization pattern.
- All rows have `from_attributes=True` — T-077 returns SQLAlchemy `Row` namedtuples from raw SQL.
- `InwardReportResponse` does NOT have `from_attributes=True` — it's constructed directly in service code with lists.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.presentation.schemas.inward_report import InwardReportResponse; InwardReportResponse.model_fields.keys()` → `{'consolidation', 'transactions'}`
- **Automated**: TC-195..TC-197 (InwardReportService.generate) return `InwardReportResponse` and assert reconciliation invariant + ordering.
- **DoD**: 3 schemas exported. `InwardConsolidationRow` and `InwardTransactionRow` have `from_attributes=True`. `place` is plain `str`. No project imports.

## Checkout

> *"schemas/inward_report.py created. 3 Pydantic v2 schemas: InwardConsolidationRow, InwardTransactionRow, InwardReportResponse. Mirrors SalesReportResponse pattern. Ready for T-077 (InwardReportService)."*
