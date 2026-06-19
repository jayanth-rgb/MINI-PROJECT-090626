from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import SupplierRepository
from src.presentation.schemas.master import SupplierCreate, SupplierRead, SupplierUpdate


class SupplierService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = SupplierRepository(session)

    def list_suppliers(self, include_inactive: bool = False) -> list[SupplierRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [SupplierRead.model_validate(r) for r in rows]

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
