from datetime import date

from sqlalchemy.orm import Session

from src.domain import stock
from src.domain.exceptions import NotFoundError
from src.infrastructure.db.repositories.master import (
    DesignGradeMapRepository,
    TradingDesignRepository,
)
from src.presentation.schemas.transactions import DesignGradeReadWithCb


class DesignGradeCbService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.design_repo = TradingDesignRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def list_active_grades_with_cb(
        self, design_id: int, stock_date: date
    ) -> list[DesignGradeReadWithCb]:
        design = self.design_repo.get(design_id)
        if not design.is_active:
            # DS-008 read semantics: a soft-deleted design is indistinguishable from missing.
            raise NotFoundError("TradingDesign", design_id)

        # list_active_by_design JOINs grade.is_active per the T-006 S1 contract.
        # AC-040 ERR-012 empty-list contract: service returns []; the frontend treats
        # an empty array as the ERR-012 trigger (per plan.md and HLD DF-003).
        rows = self.map_repo.list_active_by_design(design_id)
        return [
            DesignGradeReadWithCb(
                grade_id=row.grade_id,
                grade_code=row.grade.grade_code,
                software_cb=stock.closing_balance(
                    self.session, design_id, row.grade_id, stock_date
                ),
            )
            for row in rows
        ]
