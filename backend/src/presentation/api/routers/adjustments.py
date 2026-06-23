from fastapi import APIRouter, Depends, status

from src.application.services.adjustment_service import AdjustmentService
from src.presentation.api.dependencies import get_adjustment_service
from src.presentation.schemas.transactions import AdjustmentCreate, AdjustmentRead

router = APIRouter(prefix="/adjustments", tags=["adjustments"])


@router.post("", response_model=AdjustmentRead, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    payload: AdjustmentCreate,
    service: AdjustmentService = Depends(get_adjustment_service),
) -> AdjustmentRead:
    return service.save_adjustment(payload)
