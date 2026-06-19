# T-012 — DealerService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-012, TC-014 · **AC:** AC-007, AC-008

Mirror of T-010 with `Dealer` substitutions. Method names: `list_dealers`, `create_dealer`, `update_dealer`, `deactivate_dealer`. See T-010-plan.md for full pattern.

```python
# backend/src/application/services/dealer_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import DealerRepository
from src.presentation.schemas.master import DealerCreate, DealerUpdate, DealerRead


class DealerService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DealerRepository(session)

    def list_dealers(self, include_inactive: bool = False) -> list[DealerRead]:
        return [DealerRead.model_validate(r) for r in self.repo.list(include_inactive=include_inactive)]

    def create_dealer(self, payload: DealerCreate) -> DealerRead:
        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        return DealerRead.model_validate(obj)

    def update_dealer(self, dealer_id: int, patch: DealerUpdate) -> DealerRead:
        obj = self.repo.update(dealer_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return DealerRead.model_validate(obj)

    def deactivate_dealer(self, dealer_id: int) -> DealerRead:
        obj = self.repo.soft_delete(dealer_id)
        self.session.commit()
        return DealerRead.model_validate(obj)
```

## Checkout prompt
*"DealerService created. AC-007 + AC-008 covered."*
