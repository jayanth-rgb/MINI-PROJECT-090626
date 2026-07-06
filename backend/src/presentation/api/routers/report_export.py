"""M-010 Report Export Router — GET /reports/sales/export + GET /reports/inward/export.

Both endpoints delegate entirely to ReportExportService and wrap the returned
(BytesIO, content_type, filename) tuple in a StreamingResponse with a
Content-Disposition: attachment header (DS-021).

Mount order in main.py: this router (prefix '/reports') MUST be included
BEFORE the inward_report router (prefix '/reports/inward'). FastAPI matches
routes in registration order; including inward_report first would cause
GET /reports/inward/export to be mis-routed to inward_report's catch-all
path parameter route.

DS-007: router → service (no repository access here).
DS-021: StreamingResponse avoids fully buffering large files in memory.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.application.services.report_export_service import ReportExportService
from src.infrastructure.db.models.auth import UserModel
from src.presentation.api.dependencies import get_current_user, get_report_export_service

router = APIRouter(prefix="/reports", tags=["export"])


@router.get("/sales/export")
def export_sales_report(
    format: str = Query(..., regex="^(pdf|xlsx)$", description="Export format: pdf or xlsx"),
    date_from: Optional[date] = Query(default=None, description="Filter from date (inclusive)"),
    date_to: Optional[date] = Query(default=None, description="Filter to date (inclusive)"),
    dealer_ids: list[int] = Query(default=[], description="Filter by dealer IDs"),
    places: list[str] = Query(default=[], description="Filter by place names"),
    design_ids: list[int] = Query(default=[], description="Filter by design IDs"),
    svc: ReportExportService = Depends(get_report_export_service),
    _: UserModel = Depends(get_current_user),
) -> StreamingResponse:
    """GET /reports/sales/export — export sales report as PDF or XLSX.

    Auth: any authenticated user (all roles may export — DS-019 scope is supervisor
    only for pricing; exports are available to all authenticated roles).
    Format 400 is raised inside ReportExportService._validate_format (TC-200).

    TC-215: format=pdf → StreamingResponse, Content-Type=application/pdf, bytes start with %PDF.
    """
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
    format: str = Query(..., regex="^(pdf|xlsx)$", description="Export format: pdf or xlsx"),
    date_from: Optional[date] = Query(default=None, description="Filter from date (inclusive)"),
    date_to: Optional[date] = Query(default=None, description="Filter to date (inclusive)"),
    supplier_ids: list[int] = Query(default=[], description="Filter by supplier IDs"),
    places: list[str] = Query(default=[], description="Filter by place names"),
    design_ids: list[int] = Query(default=[], description="Filter by design IDs"),
    svc: ReportExportService = Depends(get_report_export_service),
    _: UserModel = Depends(get_current_user),
) -> StreamingResponse:
    """GET /reports/inward/export — export inward report as PDF or XLSX.

    Auth: any authenticated user.
    Format 400 is raised inside ReportExportService._validate_format.

    TC-216: format=xlsx → StreamingResponse, XLSX MIME type, bytes start with PK magic bytes.
    """
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
