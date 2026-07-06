from fastapi import APIRouter, Depends, status

from src.presentation.api.dependencies import get_pricing_service, get_current_user, require_supervisor
from src.application.services.pricing_service import PricingService
from src.presentation.schemas.pricing import PriceMasterCreate, PriceMasterRead, PriceMasterUpdate
from src.infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/prices", tags=["pricing"])


@router.get("", response_model=list[PriceMasterRead])
def list_prices(
    svc: PricingService = Depends(get_pricing_service),
    _: UserModel = Depends(get_current_user),
):
    return svc.list_prices()


@router.post("", response_model=PriceMasterRead, status_code=status.HTTP_201_CREATED)
def create_price(
    payload: PriceMasterCreate,
    svc: PricingService = Depends(get_pricing_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.create_price(payload)


@router.patch("/{price_id}", response_model=PriceMasterRead)
def update_price(
    price_id: int,
    payload: PriceMasterUpdate,
    svc: PricingService = Depends(get_pricing_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.update_price(price_id, payload)
