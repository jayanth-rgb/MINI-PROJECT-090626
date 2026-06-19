# T-021 — Designs Router (CRUD + DF-006 contract)

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** TC-036, TC-037 · **AC:** AC-013, AC-015, AC-019

## Implementation logic

```python
# backend/src/presentation/api/routers/designs.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.design_service import DesignService
from src.application.services.design_grade_map_service import DesignGradeMapService
from src.presentation.api.dependencies import get_design_service, get_design_grade_map_service
from src.presentation.schemas.master import (
    DesignCreate, DesignUpdate, DesignRead, DesignGradeReadMin,
)

router = APIRouter(prefix="/designs", tags=["designs"])


@router.get("", response_model=list[DesignRead])
def list_designs(
    include_inactive: bool = Query(False),
    service: DesignService = Depends(get_design_service),
):
    return service.list_designs(include_inactive=include_inactive)


@router.post("", response_model=DesignRead, status_code=status.HTTP_201_CREATED)
def create_design(payload: DesignCreate, service: DesignService = Depends(get_design_service)):
    return service.create_design(payload)


@router.patch("/{design_id}", response_model=DesignRead)
def update_design(design_id: int, payload: DesignUpdate, service: DesignService = Depends(get_design_service)):
    return service.update_design(design_id, payload)


@router.delete("/{design_id}", response_model=DesignRead)
def delete_design(design_id: int, service: DesignService = Depends(get_design_service)):
    return service.deactivate_design(design_id)


@router.get("/{design_id}/grades", response_model=list[DesignGradeReadMin])
def list_grades_for_design(
    design_id: int,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    # AC-019 + HLD DF-006 — minimal projection {grade_id, grade_code}, active only
    return service.list_active_grades_for_design(design_id)
```

## Constraints
- AC-019: response body for /designs/{id}/grades is EXACTLY [{grade_id, grade_code}] — no extra fields
- DS-008: DELETE -> soft
- Nested endpoint uses DesignGradeMapService (not DesignService)

## Do not touch
Any other file.

## Success criteria
- **Manual:** GET /api/v1/designs/1/grades on a seeded DB returns the active grade projection
- **Automated:** TC-036 (active projection), TC-037 (empty list)
- **DoD:** 5 endpoints (4 CRUD + 1 nested grades); DF-006 contract honored

## Checkout prompt
*"Designs router — CRUD + /designs/{id}/grades DF-006 contract delivered."*
