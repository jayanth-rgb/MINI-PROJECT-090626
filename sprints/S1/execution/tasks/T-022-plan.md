# T-022 — Design-Grade Map Router

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** TC-038 · **AC:** AC-016, AC-017

## Implementation logic

```python
# backend/src/presentation/api/routers/design_grade_map.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.design_grade_map_service import DesignGradeMapService
from src.presentation.api.dependencies import get_design_grade_map_service
from src.presentation.schemas.master import (
    DesignGradeMapCreate, DesignGradeMapUpdate, DesignGradeMapRead,
)

router = APIRouter(prefix="/design-grade-map", tags=["design-grade-map"])


@router.get("", response_model=list[DesignGradeMapRead])
def list_mappings(
    include_inactive: bool = Query(False),
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.list_mappings(include_inactive=include_inactive)


@router.post("", response_model=DesignGradeMapRead, status_code=status.HTTP_201_CREATED)
def create_mapping(
    payload: DesignGradeMapCreate,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    # ConflictError (duplicate pair) -> 409; NotFoundError (bad FK) -> 404; both via global handler.
    return service.create_mapping(payload)


@router.patch("/{map_id}", response_model=DesignGradeMapRead)
def update_mapping(
    map_id: int,
    payload: DesignGradeMapUpdate,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.update_mapping(map_id, payload)


@router.delete("/{map_id}", response_model=DesignGradeMapRead)
def delete_mapping(
    map_id: int,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.deactivate_mapping(map_id)
```

## Constraints
- AC-016: duplicate pair MUST result in HTTP 409 (via T-008 mapping)
- GET /designs/{id}/grades is NOT in this router — it's in T-021
- DS-008: DELETE -> soft

## Do not touch
Any other file.

## Success criteria
- **Manual:** Two POSTs of (10,1) -> 201 then 409
- **Automated:** TC-038 (duplicate pair 409)
- **DoD:** 4 admin CRUD endpoints; nested grades-by-design lives in T-021

## Checkout prompt
*"Design-Grade Map router — 4 admin CRUD endpoints; 409 on duplicate pair."*
