from sqlalchemy.orm import Session

from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.db.repositories.master import (
    DesignGradeMapRepository,
    GradeRepository,
    TradingDesignRepository,
)
from src.presentation.schemas.master import (
    DesignGradeMapCreate,
    DesignGradeMapRead,
    DesignGradeMapUpdate,
    DesignGradeReadMin,
)


class DesignGradeMapService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DesignGradeMapRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.grade_repo = GradeRepository(session)

    def list_mappings(self, include_inactive: bool = False) -> list[DesignGradeMapRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [self._hydrate(r) for r in rows]

    def list_active_grades_for_design(self, design_id: int) -> list[DesignGradeReadMin]:
        rows = self.repo.list_active_by_design(design_id)
        return [
            DesignGradeReadMin(grade_id=r.grade_id, grade_code=r.grade.grade_code)
            for r in rows
        ]

    def create_mapping(self, payload: DesignGradeMapCreate) -> DesignGradeMapRead:
        try:
            self.design_repo.get(payload.design_id)
        except NotFoundError:
            raise NotFoundError("TradingDesign", payload.design_id)
        try:
            self.grade_repo.get(payload.grade_id)
        except NotFoundError:
            raise NotFoundError("Grade", payload.grade_id)

        if self.repo.get_by_pair(payload.design_id, payload.grade_id) is not None:
            raise ConflictError(
                f"(design_id, grade_id) = ({payload.design_id}, {payload.grade_id}) already exists"
            )

        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        obj = self.repo.get(obj.map_id)
        return self._hydrate(obj)

    def update_mapping(self, map_id: int, patch: DesignGradeMapUpdate) -> DesignGradeMapRead:
        obj = self.repo.update(map_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return self._hydrate(obj)

    def deactivate_mapping(self, map_id: int) -> DesignGradeMapRead:
        obj = self.repo.soft_delete(map_id)
        self.session.commit()
        return self._hydrate(obj)

    @staticmethod
    def _hydrate(obj) -> DesignGradeMapRead:
        return DesignGradeMapRead(
            map_id=obj.map_id,
            design_id=obj.design_id,
            grade_id=obj.grade_id,
            is_active=obj.is_active,
            design_name=obj.design.design_name if obj.design else None,
            grade_code=obj.grade.grade_code if obj.grade else None,
        )
