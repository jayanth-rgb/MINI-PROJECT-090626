# T-018 — Staff Router

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** — · **AC:** AC-004, AC-005

## Implementation logic

```python
# backend/src/presentation/api/routers/staff.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.staff_service import StaffService
from src.presentation.api.dependencies import get_staff_service
from src.presentation.schemas.master import StaffCreate, StaffUpdate, StaffRead

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=list[StaffRead])
def list_staff(
    include_inactive: bool = Query(False),
    service: StaffService = Depends(get_staff_service),
):
    return service.list_staff(include_inactive=include_inactive)


@router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(payload: StaffCreate, service: StaffService = Depends(get_staff_service)):
    return service.create_staff(payload)


@router.patch("/{staff_id}", response_model=StaffRead)
def update_staff(staff_id: int, payload: StaffUpdate, service: StaffService = Depends(get_staff_service)):
    return service.update_staff(staff_id, payload)


@router.delete("/{staff_id}", response_model=StaffRead)
def delete_staff(staff_id: int, service: StaffService = Depends(get_staff_service)):
    return service.deactivate_staff(staff_id)
```

## Constraints
- Identical shape to T-017
- DS-008: DELETE -> soft

## Do not touch
Any other file.

## Success criteria
- **Manual:** 4 routes under /staff
- **Automated:** Covered indirectly via TC-008, TC-010 service tests
- **DoD:** Same as T-017 with Staff types

## Checkout prompt
*"Staff router — mirror of suppliers, soft DELETE."*
