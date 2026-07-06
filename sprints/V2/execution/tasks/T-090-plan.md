# T-090 — `routers/pricing.py` — Price Master CRUD

**Module:** M-011 · **Wave:** 5 (after T-089) · **Depends on:** T-083, T-089

## Context anchor

Price master data is readable by all authenticated users (GET) but only SUPERVISOR can create or update (DS-019). No DELETE endpoint — price entries are deactivated by PATCH with `{is_active: false}`. DS-022: changing a price master entry does NOT affect already-created invoice lines (unit_price is snapshotted at invoice creation time).

## Implementation logic

```python
# backend/src/presentation/api/routers/pricing.py
from fastapi import APIRouter, Depends, status

from presentation.api.dependencies import get_pricing_service, get_current_user, require_supervisor
from application.services.pricing_service import PricingService
from presentation.schemas.pricing import PriceMasterCreate, PriceMasterRead, PriceMasterUpdate
from infrastructure.db.models.auth import UserModel

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
```

## Constraints

- GET uses `get_current_user` (any authenticated role). POST/PATCH use `require_supervisor`.
- No DELETE endpoint. Deactivation is via PATCH with `{is_active: false}` using `PriceMasterUpdate` (all Optional fields, T-082).
- `svc.list_prices()` returns ALL price entries including inactive — filtering by active is a UI concern.
- `PriceMasterUpdate` all-Optional — PATCH is partial-update safe.

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.pricing import router; print(len(router.routes))"` → `3`
- **Automated**: No dedicated router TCs. TC-201 covers PricingService. Indirectly verified by TC-202..206.
- **DoD**: 3 routes. GET any-auth. POST/PATCH SUPERVISOR-only. PricingService wired.

## Checkout

> *"routers/pricing.py created. GET /prices (any auth) + POST/PATCH (SUPERVISOR-only). 3 routes. DS-019 + DS-022 respected. No DELETE — deactivate via PATCH."*
