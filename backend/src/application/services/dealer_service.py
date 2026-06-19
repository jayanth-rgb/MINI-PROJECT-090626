from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import DealerRepository
from src.presentation.schemas.master import DealerCreate, DealerRead, DealerUpdate


class DealerService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DealerRepository(session)

    def list_dealers(self, include_inactive: bool = False) -> list[DealerRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [DealerRead.model_validate(r) for r in rows]

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
