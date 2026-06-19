from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import StaffRepository
from src.presentation.schemas.master import StaffCreate, StaffRead, StaffUpdate


class StaffService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = StaffRepository(session)

    def list_staff(self, include_inactive: bool = False) -> list[StaffRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [StaffRead.model_validate(r) for r in rows]

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
