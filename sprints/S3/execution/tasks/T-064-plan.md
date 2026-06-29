# T-064 — `presentation/api/routers/dashboard.py` — GET /dashboard

**Module:** M-004 · **Depends on:** T-057, T-061, T-063

## Context anchor
Group D peer of T-065. Mirrors the existing S1/S2 router pattern (e.g. `routers/inward.py`, `routers/sales.py`). FastAPI handles ISO date parsing on the query param; 422 on missing or malformed input is the framework default — do NOT add manual validation.

## Implementation logic

```python
# backend/src/presentation/api/routers/dashboard.py
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
```

## Constraints
- Endpoint path is `""` (empty string) — combined with the router `prefix='/dashboard'` it resolves to `GET /dashboard` (so `/api/v1/dashboard` after T-066 mounts under `/api/v1`).
- `Query(...)` (Ellipsis) marks `as_of_date` required — missing → 422.
- `response_model=list[DashboardRow]` — FastAPI serializes the service's return value through the schema; do not manually call `.model_dump()`.
- No try/except. The `AssertionError` from T-061's invariant check is intentional — let it bubble to a 500. (DS-016 ledger-corruption signal.)
- No business logic in this file.

## Do not touch
- `backend/src/application/services/dashboard_service.py` (T-061)
- `backend/src/presentation/schemas/dashboard.py` (T-057)
- `backend/src/main.py` (T-066 owns the mount; do not add `include_router` here)
- Any other router

## Success criteria
- **Manual**: file imports cleanly; `router` is an `APIRouter` instance with one GET route at `""`. After T-066 mounts it, `curl http://localhost:8000/api/v1/dashboard?as_of_date=2026-06-30` returns 200.
- **Automated**: TC-117 (200 OK), TC-130 (response shape), TC-131 (missing query param → 422), TC-132 (malformed date → 422) pass.
- **DoD**: body of `list_dashboard` is a single return statement; `response_model` declared; no error handlers in this file.

## Checkout
> *"GET /dashboard router created. Pure delegation, response_model=list[DashboardRow], FastAPI handles date parsing + 422s. Ready for mount in T-066."*
