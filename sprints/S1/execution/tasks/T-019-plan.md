# T-019 — Dealers Router

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** — · **AC:** AC-007, AC-008

## Implementation logic

```python
# backend/src/presentation/api/routers/dealers.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.dealer_service import DealerService
from src.presentation.api.dependencies import get_dealer_service
from src.presentation.schemas.master import DealerCreate, DealerUpdate, DealerRead

router = APIRouter(prefix="/dealers", tags=["dealers"])


@router.get("", response_model=list[DealerRead])
def list_dealers(
    include_inactive: bool = Query(False),
    service: DealerService = Depends(get_dealer_service),
):
    return service.list_dealers(include_inactive=include_inactive)


@router.post("", response_model=DealerRead, status_code=status.HTTP_201_CREATED)
def create_dealer(payload: DealerCreate, service: DealerService = Depends(get_dealer_service)):
    return service.create_dealer(payload)


@router.patch("/{dealer_id}", response_model=DealerRead)
def update_dealer(dealer_id: int, payload: DealerUpdate, service: DealerService = Depends(get_dealer_service)):
    return service.update_dealer(dealer_id, payload)


@router.delete("/{dealer_id}", response_model=DealerRead)
def delete_dealer(dealer_id: int, service: DealerService = Depends(get_dealer_service)):
    return service.deactivate_dealer(dealer_id)
```

## Constraints
- Identical shape to T-017
- DS-008: DELETE -> soft

## Do not touch
Any other file.

## Success criteria
- **Manual:** 4 routes under /dealers
- **Automated:** Indirect via TC-012, TC-014
- **DoD:** Same as T-017 with Dealer types

## Checkout prompt
*"Dealers router — mirror of suppliers, soft DELETE."*
