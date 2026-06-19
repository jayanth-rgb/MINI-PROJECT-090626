from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import TradingDesignRepository
from src.presentation.schemas.master import DesignCreate, DesignRead, DesignUpdate


class DesignService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = TradingDesignRepository(session)

    def list_designs(self, include_inactive: bool = False) -> list[DesignRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [DesignRead.model_validate(r) for r in rows]

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
