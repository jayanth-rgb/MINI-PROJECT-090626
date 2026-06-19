# T-010 — SupplierService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-001, TC-004, TC-005, TC-006 · **AC:** AC-001, AC-002

## Implementation logic

```python
# backend/src/application/services/supplier_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import SupplierRepository
from src.presentation.schemas.master import SupplierCreate, SupplierUpdate, SupplierRead


class SupplierService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = SupplierRepository(session)

    def list_suppliers(self, include_inactive: bool = False) -> list[SupplierRead]:
        return [SupplierRead.model_validate(r) for r in self.repo.list(include_inactive=include_inactive)]

    def create_supplier(self, payload: SupplierCreate) -> SupplierRead:
        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        return SupplierRead.model_validate(obj)

    def update_supplier(self, supplier_id: int, patch: SupplierUpdate) -> SupplierRead:
        obj = self.repo.update(supplier_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return SupplierRead.model_validate(obj)

    def deactivate_supplier(self, supplier_id: int) -> SupplierRead:
        obj = self.repo.soft_delete(supplier_id)
        self.session.commit()
        return SupplierRead.model_validate(obj)
```

## Constraints
- DS-007: app layer; calls repo not raw SQL
- DS-008: deactivate uses soft_delete, never delete
- DS-012: only via BaseRepository[SupplierModel]
- Service is responsible for `session.commit()` — repository only `flush()`es (T-005)

## Do not touch
Any other file.

## Success criteria
- **Manual:** `python -c "from src.application.services.supplier_service import SupplierService; print([m for m in dir(SupplierService) if not m.startswith('_')])"` → includes `['create_supplier','deactivate_supplier','list_suppliers','update_supplier']`
- **Automated:** TC-001 (create), TC-004 (deactivate), TC-005/006 (list filter)
- **DoD:** 4 public methods; commit after each write; deactivate calls soft_delete

## Checkout prompt
*"SupplierService — list/create/update/deactivate. AC-001 + AC-002 covered."*
