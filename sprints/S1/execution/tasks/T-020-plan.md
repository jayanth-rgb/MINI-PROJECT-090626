# T-020 — Grades Router

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** TC-035 · **AC:** AC-010, AC-011, AC-012

## Implementation logic

```python
# backend/src/presentation/api/routers/grades.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.grade_service import GradeService
from src.presentation.api.dependencies import get_grade_service
from src.presentation.schemas.master import GradeCreate, GradeUpdate, GradeRead

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("", response_model=list[GradeRead])
def list_grades(
    include_inactive: bool = Query(False),
    service: GradeService = Depends(get_grade_service),
):
    return service.list_grades(include_inactive=include_inactive)


@router.post("", response_model=GradeRead, status_code=status.HTTP_201_CREATED)
def create_grade(payload: GradeCreate, service: GradeService = Depends(get_grade_service)):
    # ConflictError on duplicate grade_code -> 409 via register_error_handlers (T-008)
    return service.create_grade(payload)


@router.patch("/{grade_id}", response_model=GradeRead)
def update_grade(grade_id: int, payload: GradeUpdate, service: GradeService = Depends(get_grade_service)):
    return service.update_grade(grade_id, payload)


@router.delete("/{grade_id}", response_model=GradeRead)
def delete_grade(grade_id: int, service: GradeService = Depends(get_grade_service)):
    return service.deactivate_grade(grade_id)
```

## Constraints
- AC-011: duplicate grade_code MUST result in HTTP 409 (mapping in T-008)
- Router itself does not catch ConflictError — it propagates and the global handler returns 409
- DS-008: DELETE -> soft

## Do not touch
Any other file.

## Success criteria
- **Manual:** Two POSTs with same grade_code -> 201 then 409
- **Automated:** TC-035 (409 on duplicate)
- **DoD:** 4 endpoints; ConflictError surfaces as 409 via global handler

## Checkout prompt
*"Grades router — 4 endpoints; 409 on duplicate grade_code."*
