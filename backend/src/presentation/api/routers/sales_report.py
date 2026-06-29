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
