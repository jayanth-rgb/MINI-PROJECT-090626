# T-078 — `routers/inward_report.py` — GET /reports/inward

**Module:** M-009 · **Wave:** 5 (after T-089) · **Depends on:** T-077, T-089

## Context anchor

The inward report router returns JSON (InwardReportResponse). The export router (T-088) is SEPARATE and handles `/reports/inward/export`. Both share the `/reports` umbrella but different prefixes: this router uses prefix `/reports/inward`; export router uses prefix `/reports`. In main.py the export router MUST be registered first — otherwise FastAPI will match `/reports/inward/export` against this router's empty path before reaching the export router.

## Implementation logic

```python
# backend/src/presentation/api/routers/inward_report.py
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from presentation.api.dependencies import get_inward_report_service, get_current_user
from application.services.inward_report_service import InwardReportService
from presentation.schemas.inward_report import InwardReportResponse
from infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/reports/inward", tags=["reports"])


@router.get("", response_model=InwardReportResponse)
def get_inward_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    supplier_ids: list[int] = Query(default=[]),
    places: list[str] = Query(default=[]),
    design_ids: list[int] = Query(default=[]),
    svc: InwardReportService = Depends(get_inward_report_service),
    _: UserModel = Depends(get_current_user),
):
    return svc.generate(
        date_from=date_from,
        date_to=date_to,
        supplier_ids=supplier_ids if supplier_ids else None,
        places=places if places else None,
        design_ids=design_ids if design_ids else None,
    )
```

## Constraints

- Multi-value query params use `Query(default=[])` — FastAPI handles repeated `?supplier_ids=1&supplier_ids=2`.
- Empty list `[]` passed as `None` to service — service treats `None` as "no filter" (show all records).
- `prefix='/reports/inward'` — NOT `prefix='/reports'` + path `/inward`. Avoids ambiguity with export router.
- Auth: `get_current_user` (any role). This is NOT SUPERVISOR-only.
- InwardReportService.generate() returns an InwardReportResponse directly (Pydantic from_attributes=True in T-076).

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.inward_report import router; print(router.prefix)"` → `/reports/inward`
- **Automated**: TC-214
- **DoD**: 1 GET route. Multi-select filters. Auth required (any role). InwardReportResponse returned.

## Checkout

> *"routers/inward_report.py created. GET /reports/inward with multi-select filters (supplier_ids, places, design_ids). get_current_user guard. TC-214 covered. Mount AFTER report_export router in main.py."*
