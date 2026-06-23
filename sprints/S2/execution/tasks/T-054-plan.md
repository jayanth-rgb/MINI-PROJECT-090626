# T-054 — Adjustments router

**Module:** M-002 · **Depends on:** T-051 · **DS:** DS-007, DS-010

## Implementation logic

```python
# backend/src/presentation/api/routers/adjustments.py
from fastapi import APIRouter, Depends, status

from src.application.services.adjustment_service import AdjustmentService
from src.presentation.api.dependencies import get_adjustment_service
from src.presentation.schemas.transactions import AdjustmentCreate, AdjustmentRead

router = APIRouter(prefix="/adjustments", tags=["adjustments"])


@router.post("", response_model=AdjustmentRead, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    payload: AdjustmentCreate,
    service: AdjustmentService = Depends(get_adjustment_service),
):
    return service.save_adjustment(payload)
```

## Constraints
- DS-007: pure delegation.
- ValidationError from service (AC-035 ERR-010, AC-040 ERR-012) → 422 via global handler. No router-level catching.
- No GET endpoint in S2 — admin list of adjustments not required by ACs.

## Do not touch
Any other file.

## Success criteria
- **Manual:** OpenAPI exposes 1 endpoint.
- **Automated:** TC-076 (POST 201 + ledger = physical_cb), TC-078 (ERR-012 → 422) pass.
- **DoD:** 1 endpoint; ValidationError → 422.

## Checkout prompt
*"Adjustments router — POST /api/v1/adjustments."*
