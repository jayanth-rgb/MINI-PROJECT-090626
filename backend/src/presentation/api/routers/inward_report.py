"""M-009 Inward Report router — GET /reports/inward with multi-select filters.

Prefix: /reports/inward
Tags:   reports

Mount order note (see main.py):
  The report_export router (prefix=/reports, path=/inward/export) MUST be
  registered in main.py BEFORE this router.  FastAPI routes are matched in
  registration order; if this router is registered first, the empty-string
  path '' would consume GET /reports/inward/export before the export router
  can handle it.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.presentation.api.dependencies import get_current_user, get_inward_report_service
from src.application.services.inward_report_service import InwardReportService
from src.presentation.schemas.inward_report import InwardReportResponse
from src.infrastructure.db.models.auth import UserModel

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
) -> InwardReportResponse:
    """Return the dual-payload inward report with optional multi-select filters.

    Query parameters:
      - date_from / date_to   : inclusive date range on purchase_date
      - supplier_ids          : repeated ?supplier_ids=1&supplier_ids=2
      - places                : repeated ?places=City1&places=City2
      - design_ids            : repeated ?design_ids=10&design_ids=11

    Empty list for any multi-select param is treated as "no filter" (show all).
    Auth: any authenticated role (get_current_user guard).
    """
    return svc.generate(
        date_from=date_from,
        date_to=date_to,
        supplier_ids=supplier_ids if supplier_ids else None,
        places=places if places else None,
        design_ids=design_ids if design_ids else None,
    )
