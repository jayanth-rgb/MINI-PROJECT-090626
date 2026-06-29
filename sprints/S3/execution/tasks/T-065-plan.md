# T-065 — `presentation/api/routers/sales_report.py` — GET /reports/sales

**Module:** M-005 · **Depends on:** T-058, T-062, T-063 · **DS:** DS-017 (inherited from service)

## Context anchor
Group D peer of T-064. The multi-select filter pattern mirrors **T-053's `list_sales` from S2** — FastAPI handles repeat-key query strings (`?dealer_ids=1&dealer_ids=2`) natively as `list[int]` parameters; no manual parsing required.

## Implementation logic

```python
# backend/src/presentation/api/routers/sales_report.py
from datetime import date

from fastapi import APIRouter, Depends, Query

from src.application.services.sales_report_service import SalesReportService
from src.presentation.api.dependencies import get_sales_report_service
from src.presentation.schemas.sales_report import SalesReportResponse

router = APIRouter(prefix="/reports/sales", tags=["reports"])


@router.get("", response_model=SalesReportResponse)
def get_sales_report(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    dealer_ids: list[int] | None = Query(default=None),
    places: list[str] | None = Query(default=None),
    design_ids: list[int] | None = Query(default=None),
    service: SalesReportService = Depends(get_sales_report_service),
) -> SalesReportResponse:
    return service.generate(
        date_from=date_from,
        date_to=date_to,
        dealer_ids=dealer_ids,
        places=places,
        design_ids=design_ids,
    )
```

## Constraints
- All 5 filter params optional (RULE-018) — `Query(default=None)`, NOT `Query(...)`.
- Lists declared as `list[int] | None` / `list[str] | None` — FastAPI's native repeat-key parsing. **Do not** accept comma-separated strings; that would force manual splitting and break parity with T-053.
- `response_model=SalesReportResponse` — FastAPI handles the dual-payload serialization.
- No try/except — `AssertionError` from T-062's AC-050 check should bubble to 500 (it indicates real data corruption).
- No business logic — pure delegation.

## Do not touch
- `backend/src/application/services/sales_report_service.py` (T-062)
- `backend/src/presentation/schemas/sales_report.py` (T-058)
- `backend/src/main.py` (T-066 owns the mount)
- Any other router

## Success criteria
- **Manual**: `curl 'http://localhost:8000/api/v1/reports/sales'` returns 200 with `{consolidation:[], transactions:[]}`. `curl 'http://localhost:8000/api/v1/reports/sales?dealer_ids=1&dealer_ids=2&places=Mysuru&date_from=2026-06-01'` filters correctly.
- **Automated**: TC-140 + TC-147 + TC-148 + TC-149 + TC-158 pass.
- **DoD**: body of `get_sales_report` is a single `return service.generate(...)` call passing every Query through as a keyword arg; `response_model` declared.

## Checkout
> *"GET /reports/sales router created. Multi-select via repeated query keys (FastAPI native parsing — matches T-053 pattern), response_model=SalesReportResponse. Ready for mount in T-066."*
