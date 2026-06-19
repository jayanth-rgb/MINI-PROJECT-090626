# T-011 — StaffService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-008, TC-010 · **AC:** AC-004, AC-005

## Implementation logic

Mirror of T-010 (SupplierService) with substitutions:
- `SupplierRepository` → `StaffRepository`
- `SupplierCreate/Update/Read` → `StaffCreate/Update/Read`
- Method names: `list_staff`, `create_staff`, `update_staff`, `deactivate_staff`

```python
# backend/src/application/services/staff_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import StaffRepository
from src.presentation.schemas.master import StaffCreate, StaffUpdate, StaffRead


class StaffService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = StaffRepository(session)

    def list_staff(self, include_inactive: bool = False) -> list[StaffRead]:
        return [StaffRead.model_validate(r) for r in self.repo.list(include_inactive=include_inactive)]

    def create_staff(self, payload: StaffCreate) -> StaffRead:
        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        return StaffRead.model_validate(obj)

    def update_staff(self, staff_id: int, patch: StaffUpdate) -> StaffRead:
        obj = self.repo.update(staff_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return StaffRead.model_validate(obj)

    def deactivate_staff(self, staff_id: int) -> StaffRead:
        obj = self.repo.soft_delete(staff_id)
        self.session.commit()
        return StaffRead.model_validate(obj)
```

## Constraints / Do not touch / Success criteria
Identical to T-010 with staff substitutions. See T-010-plan.md.

## Checkout prompt
*"StaffService created. AC-004 + AC-005 covered."*
