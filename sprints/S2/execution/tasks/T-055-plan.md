# T-055 — Add `GET /designs/{id}/grades-with-cb` to designs router

**Module:** M-002 · **Depends on:** T-051, T-050 · **DS:** DS-007, DS-010

## Implementation logic

Append to the existing `designs.py` router (after all existing routes):

```python
from datetime import date
from src.application.services.design_grade_cb_service import DesignGradeCbService
from src.presentation.api.dependencies import get_design_grade_cb_service
from src.presentation.schemas.transactions import DesignGradeReadWithCb


@router.get("/{design_id}/grades-with-cb", response_model=list[DesignGradeReadWithCb])
def list_grades_with_cb_for_design(
    design_id: int,
    stock_date: date = Query(...),
    service: DesignGradeCbService = Depends(get_design_grade_cb_service),
):
    return service.list_active_grades_with_cb(design_id, stock_date)
```

## Constraints
- DO NOT modify any existing route (CRUD or /grades).
- `stock_date` is a REQUIRED query param (`Query(...)`); FastAPI returns 422 if missing.
- Response: empty array `[]` is the contract when no active grades exist — NOT 404 / 422 (per LLD note; the FORM converts `[]` to ERR-012, not the API).

## Do not touch
Any other file. Any existing route in designs.py.

## Success criteria
- **Manual:** OpenAPI shows the new route.
- **Automated:** TC-071 passes.
- **DoD:** 1 new route; `response_model=list[DesignGradeReadWithCb]` strips extras.

## Checkout prompt
*"Designs router extended — GET /{id}/grades-with-cb wired."*
