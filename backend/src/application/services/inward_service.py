from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain import stock
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.db.models.transactions import InwardHeaderModel
from src.infrastructure.db.repositories.master import (
    DesignGradeMapRepository,
    GradeRepository,
    StaffRepository,
    SupplierRepository,
    TradingDesignRepository,
)
from src.infrastructure.db.repositories.transactions import InwardHeaderRepository
from src.presentation.schemas.transactions import InwardCreate, InwardRead

MAX_BACKDATE_DAYS = 7


class InwardService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = InwardHeaderRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.staff_repo = StaffRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.grade_repo = GradeRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def save_inward(self, payload: InwardCreate) -> InwardRead:
        today_ = date.today()

        # AC-020 / ERR-001: future-date rejection.
        if payload.purchase_date > today_:
            raise ValidationError("purchase_date cannot be in the future")
        # AC-021 / ERR-002: > 7-day-prior rejection.
        if payload.purchase_date < today_ - timedelta(days=MAX_BACKDATE_DAYS):
            raise ValidationError(
                f"purchase_date cannot be older than {MAX_BACKDATE_DAYS} days"
            )

        # AC-022 / DS-013: supplier must exist + be active; snapshot place.
        supplier = self.supplier_repo.get(payload.supplier_id)
        if not supplier.is_active:
            raise ValidationError(f"Supplier {payload.supplier_id} is inactive")

        # Entered-by staff active check.
        staff = self.staff_repo.get(payload.entered_by_id)
        if not staff.is_active:
            raise ValidationError(f"Staff {payload.entered_by_id} is inactive")

        # RULE-017 / AC-025: strip None/zero lines silently.
        kept_lines = [
            line for line in payload.lines if line.nos is not None and line.nos > 0
        ]
        # AC-026 / ERR-008: must have ≥ 1 valid line after stripping.
        if not kept_lines:
            raise ValidationError("at least one line with nos > 0 required")

        # AC-023 / ERR-005: each (design, grade) pair must be in active design_grade_map.
        for line in kept_lines:
            design = self.design_repo.get(line.design_id)
            if not design.is_active:
                raise ValidationError(f"Design {line.design_id} is inactive")
            grade = self.grade_repo.get(line.grade_id)
            if not grade.is_active:
                raise ValidationError(f"Grade {line.grade_id} is inactive")
            pair = self.map_repo.get_by_pair(line.design_id, line.grade_id)
            if pair is None or not pair.is_active:
                raise ValidationError(
                    f"(design_id, grade_id) = ({line.design_id}, {line.grade_id}) "
                    "is not an active mapping"
                )

        # Persist header + lines in one flush.
        header = self.repo.create_with_lines(
            header_payload={
                "purchase_date": payload.purchase_date,
                "supplier_id": payload.supplier_id,
                "place": supplier.place,  # DS-013 snapshot
                "entered_by_id": payload.entered_by_id,
            },
            line_payloads=[
                {"design_id": line.design_id, "grade_id": line.grade_id, "nos": line.nos}
                for line in kept_lines
            ],
        )

        # DS-002 / DS-003: per-line ledger write — each call acquires SELECT FOR UPDATE
        # on the latest row for (design, grade) before computing the new running_balance.
        for line in header.lines:
            stock.apply_inward(
                self.session,
                line.design_id,
                line.grade_id,
                payload.purchase_date,
                line.nos,
                header.header_id,
                line.line_id,
            )

        # AC-027: header + lines + ledger rows persist as one atomic transaction.
        self.session.commit()
        return InwardRead.model_validate(header)

    def list_inwards(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[InwardRead]:
        stmt = select(InwardHeaderModel)
        if date_from is not None:
            stmt = stmt.where(InwardHeaderModel.purchase_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(InwardHeaderModel.purchase_date <= date_to)
        stmt = stmt.order_by(
            InwardHeaderModel.purchase_date.desc(),
            InwardHeaderModel.header_id.desc(),
        )
        # .unique() collapses the row multiplication caused by lazy='joined' on .lines.
        headers = self.session.execute(stmt).scalars().unique().all()
        return [InwardRead.model_validate(h) for h in headers]
