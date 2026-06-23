from datetime import date

from fastapi import APIRouter, Depends, Query, status

from src.application.services.sales_service import SalesService
from src.presentation.api.dependencies import get_sales_service
from src.presentation.schemas.transactions import SalesCreate, SalesRead

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SalesRead, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SalesCreate,
    service: SalesService = Depends(get_sales_service),
) -> SalesRead:
    return service.save_sale(payload)


@router.get("", response_model=list[SalesRead])
def list_sales(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    dealer_ids: list[int] | None = Query(default=None),
    design_ids: list[int] | None = Query(default=None),
    service: SalesService = Depends(get_sales_service),
) -> list[SalesRead]:
    return service.list_sales(
        date_from=date_from,
        date_to=date_to,
        dealer_ids=dealer_ids,
        design_ids=design_ids,
    )
