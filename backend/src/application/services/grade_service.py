from sqlalchemy.orm import Session

from src.domain.exceptions import ConflictError
from src.infrastructure.db.repositories.master import GradeRepository
from src.presentation.schemas.master import GradeCreate, GradeRead, GradeUpdate


class GradeService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = GradeRepository(session)

    def list_grades(self, include_inactive: bool = False) -> list[GradeRead]:
        rows = self.repo.list(include_inactive=include_inactive)
        return [GradeRead.model_validate(r) for r in rows]

    def create_grade(self, payload: GradeCreate) -> GradeRead:
        # AC-011: pre-check uniqueness. Strip whitespace first so '  DIM  ' and
        # 'DIM' are treated as the same code (resolves N-001 from T-007 critique).
        code = payload.grade_code.strip()
        if self.repo.get_by_code(code) is not None:
            raise ConflictError(f"grade_code '{code}' already exists")
        obj = self.repo.create({"grade_code": code})
        self.session.commit()
        return GradeRead.model_validate(obj)

    def update_grade(self, grade_id: int, patch: GradeUpdate) -> GradeRead:
        data = patch.model_dump(exclude_none=True)
        if "grade_code" in data:
            # Normalise + check uniqueness, excluding the row being updated.
            data["grade_code"] = data["grade_code"].strip()
            existing = self.repo.get_by_code(data["grade_code"])
            if existing is not None and existing.grade_id != grade_id:
                raise ConflictError(
                    f"grade_code '{data['grade_code']}' already exists"
                )
        obj = self.repo.update(grade_id, data)
        self.session.commit()
        return GradeRead.model_validate(obj)

    def deactivate_grade(self, grade_id: int) -> GradeRead:
        obj = self.repo.soft_delete(grade_id)
        self.session.commit()
        return GradeRead.model_validate(obj)
