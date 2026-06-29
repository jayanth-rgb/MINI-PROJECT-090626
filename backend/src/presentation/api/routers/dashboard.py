from datetime import date

from fastapi import APIRouter, Depends, Query

from src.application.services.dashboard_service import DashboardService
from src.presentation.api.dependencies import get_dashboard_service
from src.presentation.schemas.dashboard import DashboardRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=list[DashboardRow])
def list_dashboard(
    as_of_date: date = Query(..., description="As-of date for the stock dashboard"),
    service: DashboardService = Depends(get_dashboard_service),
) -> list[DashboardRow]:
    return service.list_as_of(as_of_date)
