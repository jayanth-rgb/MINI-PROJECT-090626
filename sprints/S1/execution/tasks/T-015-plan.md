# T-015 — DesignGradeMapService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-024, 025, 027, 028, 029, 031, 032 · **AC:** AC-016, AC-017, AC-019

This is the most invariant-heavy service in S1. AC-019 delivers the DF-006 contract S2 transaction forms will consume.

## Implementation logic

```python
# backend/src/application/services/design_grade_map_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import (
    DesignGradeMapRepository, TradingDesignRepository, GradeRepository,
)
from src.presentation.schemas.master import (
    DesignGradeMapCreate, DesignGradeMapUpdate, DesignGradeMapRead, DesignGradeReadMin,
)
from src.domain.exceptions import NotFoundError, ConflictError


class DesignGradeMapService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DesignGradeMapRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.grade_repo = GradeRepository(session)

    def list_mappings(self, include_inactive: bool = False) -> list[DesignGradeMapRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [
            DesignGradeMapRead(
                map_id=r.map_id,
                design_id=r.design_id,
                grade_id=r.grade_id,
                is_active=r.is_active,
                design_name=r.design.design_name if r.design else None,
                grade_code=r.grade.grade_code if r.grade else None,
            )
            for r in rows
        ]

    def list_active_grades_for_design(self, design_id: int) -> list[DesignGradeReadMin]:
        # AC-019 — DF-006 contract S2 forms depend on. Repo filters BOTH map.is_active AND grade.is_active.
        rows = self.repo.list_active_by_design(design_id)
        return [DesignGradeReadMin(grade_id=r.grade_id, grade_code=r.grade.grade_code) for r in rows]

    def create_mapping(self, payload: DesignGradeMapCreate) -> DesignGradeMapRead:
        # AC-016: pre-check FK existence and uniqueness
        if self.design_repo.list(include_inactive=True) and not any(
            d.design_id == payload.design_id for d in self.design_repo.list(include_inactive=True)
        ):
            raise NotFoundError("TradingDesign", payload.design_id)
        # Better: catch NotFoundError from get
        try:
            self.design_repo.get(payload.design_id)
        except NotFoundError:
            raise NotFoundError("TradingDesign", payload.design_id)
        try:
            self.grade_repo.get(payload.grade_id)
        except NotFoundError:
            raise NotFoundError("Grade", payload.grade_id)

        if self.repo.get_by_pair(payload.design_id, payload.grade_id) is not None:
            raise ConflictError(f"(design_id, grade_id) = ({payload.design_id}, {payload.grade_id}) already exists")

        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        # re-load with joined design/grade for hydrated read
        obj = self.repo.get(obj.map_id)
        return DesignGradeMapRead(
            map_id=obj.map_id,
            design_id=obj.design_id,
            grade_id=obj.grade_id,
            is_active=obj.is_active,
            design_name=obj.design.design_name if obj.design else None,
            grade_code=obj.grade.grade_code if obj.grade else None,
        )

    def update_mapping(self, map_id: int, patch: DesignGradeMapUpdate) -> DesignGradeMapRead:
        obj = self.repo.update(map_id, patch.model_dump(exclude_none=True))
        self.session.commit()
        return DesignGradeMapRead(
            map_id=obj.map_id, design_id=obj.design_id, grade_id=obj.grade_id, is_active=obj.is_active,
            design_name=obj.design.design_name if obj.design else None,
            grade_code=obj.grade.grade_code if obj.grade else None,
        )

    def deactivate_mapping(self, map_id: int) -> DesignGradeMapRead:
        obj = self.repo.soft_delete(map_id)
        self.session.commit()
        return DesignGradeMapRead(
            map_id=obj.map_id, design_id=obj.design_id, grade_id=obj.grade_id, is_active=obj.is_active,
            design_name=obj.design.design_name if obj.design else None,
            grade_code=obj.grade.grade_code if obj.grade else None,
        )
```

## Constraints
- AC-019 (TC-019, TC-031): JOIN filter is in T-006 repo, not duplicated here
- AC-016 (TC-027, TC-028): NotFoundError messages MUST include 'TradingDesign' / 'Grade'
- AC-016 (TC-025): ConflictError message MUST include 'design_id, grade_id'
- AC-017 (TC-029): deactivate uses soft_delete; row physically present

## Checkout prompt
*"DesignGradeMapService — 5 methods including AC-019 contract. F-006 covered."*
