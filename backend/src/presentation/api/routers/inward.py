from datetime import date

from fastapi import APIRouter, Depends, Query, status

from src.application.services.inward_service import InwardService
from src.presentation.api.dependencies import get_inward_service
from src.presentation.schemas.transactions import InwardCreate, InwardRead

router = APIRouter(prefix="/inward", tags=["inward"])


@router.post("", response_model=InwardRead, status_code=status.HTTP_201_CREATED)
def create_inward(
    payload: InwardCreate,
    service: InwardService = Depends(get_inward_service),
) -> InwardRead:
    return service.save_inward(payload)


@router.get("", response_model=list[InwardRead])
def list_inwards(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    service: InwardService = Depends(get_inward_service),
) -> list[InwardRead]:
    return service.list_inwards(date_from=date_from, date_to=date_to)
