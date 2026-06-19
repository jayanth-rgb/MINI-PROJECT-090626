# T-013 — GradeService

**Module:** M-001 · **Depends on:** T-006, T-007, T-003 · **TC refs:** TC-017, TC-019 · **AC:** AC-011, AC-012

## Implementation logic — DIFFERS from supplier shape

Pre-check uniqueness BEFORE INSERT to surface a friendly ConflictError. The DB still enforces UNIQUE (T-004) as a safety net for races.

```python
# backend/src/application/services/grade_service.py
from sqlalchemy.orm import Session

from src.infrastructure.db.repositories.master import GradeRepository
from src.presentation.schemas.master import GradeCreate, GradeUpdate, GradeRead
from src.domain.exceptions import ConflictError


class GradeService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = GradeRepository(session)

    def list_grades(self, include_inactive: bool = False) -> list[GradeRead]:
        return [GradeRead.model_validate(r) for r in self.repo.list(include_inactive=include_inactive)]

    def create_grade(self, payload: GradeCreate) -> GradeRead:
        # AC-011: pre-check uniqueness
        if self.repo.get_by_code(payload.grade_code) is not None:
            raise ConflictError(f"grade_code '{payload.grade_code}' already exists")
        obj = self.repo.create(payload.model_dump())
        self.session.commit()
        return GradeRead.model_validate(obj)

    def update_grade(self, grade_id: int, patch: GradeUpdate) -> GradeRead:
        data = patch.model_dump(exclude_none=True)
        if "grade_code" in data:
            existing = self.repo.get_by_code(data["grade_code"])
            if existing is not None and existing.grade_id != grade_id:
                raise ConflictError(f"grade_code '{data['grade_code']}' already exists")
        obj = self.repo.update(grade_id, data)
        self.session.commit()
        return GradeRead.model_validate(obj)

    def deactivate_grade(self, grade_id: int) -> GradeRead:
        obj = self.repo.soft_delete(grade_id)
        self.session.commit()
        return GradeRead.model_validate(obj)
```

## Constraints
- AC-011: ConflictError message MUST include 'grade_code' so TC-035 body assertion passes
- AC-012: deactivate is soft-delete; interlocking effect on design-grade list is in T-015's `list_active_grades_for_design`
- update_grade: don't compare against self when checking duplicate (handle the rename-to-same case)

## Checkout prompt
*"GradeService created with uniqueness pre-check. AC-011 + AC-012 covered."*
