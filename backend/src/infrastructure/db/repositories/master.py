from sqlalchemy import select

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[SupplierModel]):
    pass


class StaffRepository(BaseRepository[StaffModel]):
    pass


class DealerRepository(BaseRepository[DealerModel]):
    pass


class GradeRepository(BaseRepository[GradeModel]):
    def get_by_code(self, code: str) -> GradeModel | None:
        return self.session.execute(
            select(GradeModel).where(GradeModel.grade_code == code)
        ).scalar_one_or_none()


class TradingDesignRepository(BaseRepository[TradingDesignModel]):
    pass


class DesignGradeMapRepository(BaseRepository[DesignGradeMapModel]):
    def get_by_pair(self, design_id: int, grade_id: int) -> DesignGradeMapModel | None:
        return self.session.execute(
            select(DesignGradeMapModel).where(
                DesignGradeMapModel.design_id == design_id,
                DesignGradeMapModel.grade_id == grade_id,
            )
        ).scalar_one_or_none()

    def list_active_by_design(self, design_id: int) -> list[DesignGradeMapModel]:
        # AC-019: filter BOTH map.is_active AND grade.is_active via JOIN.
        stmt = (
            select(DesignGradeMapModel)
            .join(GradeModel, GradeModel.grade_id == DesignGradeMapModel.grade_id)
            .where(
                DesignGradeMapModel.design_id == design_id,
                DesignGradeMapModel.is_active.is_(True),
                GradeModel.is_active.is_(True),
            )
        )
        return list(self.session.execute(stmt).scalars())
