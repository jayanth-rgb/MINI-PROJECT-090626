# T-052 — Inward router

**Module:** M-002 · **Depends on:** T-051 · **DS:** DS-007, DS-010

## Implementation logic

```python
# backend/src/presentation/api/routers/inward.py
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
):
    return service.save_inward(payload)


@router.get("", response_model=list[InwardRead])
def list_inwards(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    service: InwardService = Depends(get_inward_service),
):
    return service.list_inwards(date_from=date_from, date_to=date_to)
```

## Constraints
- DS-007: pure delegation. No business logic in the router.
- DS-010: prefix `/inward`; `/api/v1` prepended by `main.py`.
- ValidationError → 422 via S1's `register_error_handlers` (T-008). NotFoundError → 404. No router-level catching.

## Do not touch
Any other file.

## Success criteria
- **Manual:** OpenAPI shows POST and GET under /api/v1/inward.
- **Automated:** TC-048 (future date → 422) and TC-057 (POST 201 + ledger increases) pass.
- **DoD:** 2 endpoints; clean delegation; exception propagation.

## Checkout prompt
*"Inward router — POST + GET on /api/v1/inward."*
