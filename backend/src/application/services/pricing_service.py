from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.db.models.master import GradeModel, TradingDesignModel
from src.infrastructure.db.models.pricing import PriceMasterModel
from src.infrastructure.db.repositories.pricing import PriceMasterRepository
from src.presentation.schemas.pricing import (
    PriceMasterCreate,
    PriceMasterRead,
    PriceMasterUpdate,
)


class PricingService:

    def __init__(self, db: Session) -> None:
        self._repo = PriceMasterRepository(db)
        self._db = db

    @staticmethod
    def _to_read(price: PriceMasterModel) -> PriceMasterRead:
        return PriceMasterRead(
            id=price.id,
            design_id=price.design_id,
            design_name=price.design.design_name,
            size=price.design.size,
            grade_id=price.grade_id,
            grade_code=price.grade.grade_code,
            unit_price=price.unit_price,
            effective_from=price.effective_from,
            is_active=price.is_active,
        )

    def list_prices(self) -> list[PriceMasterRead]:
        return [self._to_read(p) for p in self._repo.list_all()]

    def create_price(self, data: PriceMasterCreate) -> PriceMasterRead:
        if self._db.get(TradingDesignModel, data.design_id) is None:
            raise NotFoundError("TradingDesign", data.design_id)
        if self._db.get(GradeModel, data.grade_id) is None:
            raise NotFoundError("Grade", data.grade_id)
        existing = self._db.scalar(
            select(PriceMasterModel).where(
                PriceMasterModel.design_id == data.design_id,
                PriceMasterModel.grade_id == data.grade_id,
                PriceMasterModel.effective_from == data.effective_from,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"Price already exists for design={data.design_id}, grade={data.grade_id},"
                f" effective_from={data.effective_from}"
            )
        price = self._repo.create({
            "design_id": data.design_id,
            "grade_id": data.grade_id,
            "unit_price": data.unit_price,
            "effective_from": data.effective_from,
            "is_active": True,
        })
        self._db.commit()
        return self._to_read(price)

    def update_price(self, price_id: int, data: PriceMasterUpdate) -> PriceMasterRead:
        price = self._repo.update(price_id, data.model_dump(exclude_none=True))
        self._db.commit()
        return self._to_read(price)
