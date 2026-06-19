# T-014 — DesignService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-020, TC-023 · **AC:** AC-013, AC-015

Mirror of T-010 (SupplierService) with `TradingDesign` substitutions.

```python
# backend/src/application/services/design_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import TradingDesignRepository
from src.presentation.schemas.master import DesignCreate, DesignUpdate, DesignRead


class DesignService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = TradingDesignRepository(session)

    def list_designs(self, include_inactive: bool = False) -> list[DesignRead]:
        return [DesignRead.model_validate(r) for r in self.repo.list(include_inactive=include_inactive)]

    def create_design(self, payload: DesignCreate) -> DesignRead:
        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        return DesignRead.model_validate(obj)

    def update_design(self, design_id: int, patch: DesignUpdate) -> DesignRead:
        obj = self.repo.update(design_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return DesignRead.model_validate(obj)

    def deactivate_design(self, design_id: int) -> DesignRead:
        obj = self.repo.soft_delete(design_id)
        self.session.commit()
        return DesignRead.model_validate(obj)
```

## Checkout prompt
*"DesignService created. AC-013 + AC-015 covered."*
