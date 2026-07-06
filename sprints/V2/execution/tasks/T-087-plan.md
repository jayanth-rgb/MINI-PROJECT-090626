# T-087 — `services/report_export_service.py` — ReportExportService

**Module:** M-010 · **Wave:** 3 (after T-077, T-085, T-086) · **Depends on:** T-077, T-085, T-086

## Context anchor

Orchestrates report generation + export format routing. Reads data from `SalesReportService` (S3, existing) or `InwardReportService` (T-077, this sprint), then passes to `PdfExporter` or `ExcelExporter`. The router (T-088) calls this service and wraps the result in `StreamingResponse`.

## Implementation logic

```python
# backend/src/application/services/report_export_service.py
from datetime import date
from io import BytesIO
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from application.services.sales_report_service import SalesReportService
from application.services.inward_report_service import InwardReportService
from infrastructure.exporters.pdf_exporter import PdfExporter
from infrastructure.exporters.excel_exporter import ExcelExporter

_PDF_MIME = "application/pdf"
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ReportExportService:

    def __init__(self, db: Session) -> None:
        self._db = db

    def export_sales(
        self,
        format: str,
        date_from: date | None = None,
        date_to: date | None = None,
        dealer_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> tuple[BytesIO, str, str]:
        if format not in ("pdf", "xlsx"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Unsupported format '{format}'. Use 'pdf' or 'xlsx'.")
        filters = dict(
            date_from=date_from, date_to=date_to,
            dealer_ids=dealer_ids, places=places, design_ids=design_ids
        )
        data = SalesReportService(self._db).generate(
            date_from=date_from, date_to=date_to,
            dealer_ids=dealer_ids, places=places, design_ids=design_ids
        )
        today_str = date.today().strftime("%Y-%m-%d")
        if format == "pdf":
            buf = PdfExporter().export_sales_report(data, filters)
            return buf, _PDF_MIME, f"sales_report_{today_str}.pdf"
        else:
            buf = ExcelExporter().export_sales_report(data, filters)
            return buf, _XLSX_MIME, f"sales_report_{today_str}.xlsx"

    def export_inward(
        self,
        format: str,
        date_from: date | None = None,
        date_to: date | None = None,
        supplier_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> tuple[BytesIO, str, str]:
        if format not in ("pdf", "xlsx"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Unsupported format '{format}'. Use 'pdf' or 'xlsx'.")
        filters = dict(
            date_from=date_from, date_to=date_to,
            supplier_ids=supplier_ids, places=places, design_ids=design_ids
        )
        data = InwardReportService(self._db).generate(
            date_from=date_from, date_to=date_to,
            supplier_ids=supplier_ids, places=places, design_ids=design_ids
        )
        today_str = date.today().strftime("%Y-%m-%d")
        if format == "pdf":
            buf = PdfExporter().export_inward_report(data, filters)
            return buf, _PDF_MIME, f"inward_report_{today_str}.pdf"
        else:
            buf = ExcelExporter().export_inward_report(data, filters)
            return buf, _XLSX_MIME, f"inward_report_{today_str}.xlsx"
```

## Constraints

- Format validation happens FIRST before any DB call — fail fast on invalid input.
- `PdfExporter` and `ExcelExporter` are instantiated per-call (stateless) — no shared state risk.
- `SalesReportService` import path: `application.services.sales_report_service` (S3 file, existing).
- `InwardReportService` import path: `application.services.inward_report_service` (T-077, this sprint).
- Returns `(BytesIO, content_type, filename)` tuple — the router wraps this in `StreamingResponse`.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.application.services.report_export_service import ReportExportService; print('ok')`
- **Automated**: TC-200 (format='csv' → HTTPException 400).
- **DoD**: 2 methods. HTTPException 400 on unsupported format. Returns 3-tuple. Filename includes YYYY-MM-DD.

## Checkout

> *"ReportExportService created. export_sales + export_inward. Format validation (400 on unsupported). TC-200 covered. Ready for T-088 (router) and T-089 (dependencies.py)."*
