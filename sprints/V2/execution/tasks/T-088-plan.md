# T-088 — `routers/report_export.py` — GET /reports/sales/export · GET /reports/inward/export

**Module:** M-010 · **Wave:** 5 (after T-089) · **Depends on:** T-087, T-089

## Context anchor

Export router uses `prefix='/reports'`. In main.py it MUST be registered BEFORE the inward report router (prefix `/reports/inward`) to prevent FastAPI mis-routing `/reports/inward/export` as a match for inward report's GET `""` path. StreamingResponse streams the BytesIO buffer — no additional buffering. 400 on unsupported format is raised inside ReportExportService (T-087), not in the router.

## Implementation logic

```python
# backend/src/presentation/api/routers/report_export.py
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from presentation.api.dependencies import get_report_export_service, get_current_user
from application.services.report_export_service import ReportExportService
from infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales/export")
def export_sales_report(
    format: str = Query(..., description="pdf or xlsx"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    dealer_ids: list[int] = Query(default=[]),
    places: list[str] = Query(default=[]),
    design_ids: list[int] = Query(default=[]),
    svc: ReportExportService = Depends(get_report_export_service),
    _: UserModel = Depends(get_current_user),
):
    buf, content_type, filename = svc.export_sales(
        format=format,
        date_from=date_from,
        date_to=date_to,
        dealer_ids=dealer_ids if dealer_ids else None,
        places=places if places else None,
        design_ids=design_ids if design_ids else None,
    )
    return StreamingResponse(
        buf,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/inward/export")
def export_inward_report(
    format: str = Query(..., description="pdf or xlsx"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    supplier_ids: list[int] = Query(default=[]),
    places: list[str] = Query(default=[]),
    design_ids: list[int] = Query(default=[]),
    svc: ReportExportService = Depends(get_report_export_service),
    _: UserModel = Depends(get_current_user),
):
    buf, content_type, filename = svc.export_inward(
        format=format,
        date_from=date_from,
        date_to=date_to,
        supplier_ids=supplier_ids if supplier_ids else None,
        places=places if places else None,
        design_ids=design_ids if design_ids else None,
    )
    return StreamingResponse(
        buf,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

## Constraints

- **Mount order in main.py**: this router (prefix `/reports`) BEFORE inward_report router (prefix `/reports/inward`). FastAPI matches routes in registration order.
- `StreamingResponse` wraps the `BytesIO` directly — buffer is already seeked to 0 by the exporter (T-085/T-086 guarantee this).
- `format` is a required query param (`...`). 400 on unsupported format is raised inside ReportExportService — the router does not validate format itself.
- No `response_model` on StreamingResponse routes — FastAPI cannot serialize binary responses.
- Auth: `get_current_user` (any authenticated role can export).
- Empty list params converted to `None` before passing to service (same pattern as inward_report router).

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.report_export import router; print(router.prefix)"` → `/reports`
- **Automated**: TC-215, TC-216
- **DoD**: 2 routes. StreamingResponse returned. Content-Disposition attachment set. Auth required. Format 400 handled at service layer.

## Checkout

> *"routers/report_export.py created. GET /reports/sales/export + /inward/export. StreamingResponse with Content-Disposition (DS-021). TC-215/216 covered. CRITICAL: include this router BEFORE inward_report router in main.py (T-092)."*
