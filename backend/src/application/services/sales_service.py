from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain import stock
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from src.infrastructure.db.repositories.master import (
    DealerRepository,
    DesignGradeMapRepository,
    GradeRepository,
    StaffRepository,
    TradingDesignRepository,
)
from src.infrastructure.db.repositories.transactions import SalesHeaderRepository
from src.presentation.schemas.transactions import SalesCreate, SalesRead

MAX_BACKDATE_DAYS = 7


class SalesService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = SalesHeaderRepository(session)
        self.dealer_repo = DealerRepository(session)
        self.staff_repo = StaffRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.grade_repo = GradeRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def save_sale(self, payload: SalesCreate) -> SalesRead:
        today_ = date.today()

        # AC-028 / ERR-001 / ERR-002: same date-bounds window as inward.
        if payload.sales_date > today_:
            raise ValidationError("sales_date cannot be in the future")
        if payload.sales_date < today_ - timedelta(days=MAX_BACKDATE_DAYS):
            raise ValidationError(
                f"sales_date cannot be older than {MAX_BACKDATE_DAYS} days"
            )

        # AC-029 / DS-013: dealer must exist + be active; snapshot place.
        dealer = self.dealer_repo.get(payload.dealer_id)
        if not dealer.is_active:
            raise ValidationError(f"Dealer {payload.dealer_id} is inactive")

        # AC-030: BOTH loading_staff_id AND verified_by_id required (Pydantic) + active (here).
        # Same staff for both roles is permitted by the spec.
        for staff_id in (payload.loading_staff_id, payload.verified_by_id):
            staff = self.staff_repo.get(staff_id)
            if not staff.is_active:
                raise ValidationError(f"Staff {staff_id} is inactive")

        # RULE-017 / AC-025-equivalent: strip None/zero lines silently.
        kept_lines = [
            line for line in payload.lines if line.nos is not None and line.nos > 0
        ]
        # AC-026-equivalent: must have ≥ 1 valid line.
        if not kept_lines:
            raise ValidationError("at least one line with nos > 0 required")

        # AC-031 / ERR-005: each (design, grade) pair must be in active design_grade_map.
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
                "sales_date": payload.sales_date,
                "dealer_id": payload.dealer_id,
                "place": dealer.place,  # DS-013 snapshot
                "loading_staff_id": payload.loading_staff_id,
                "verified_by_id": payload.verified_by_id,
            },
            line_payloads=[
                {"design_id": line.design_id, "grade_id": line.grade_id, "nos": line.nos}
                for line in kept_lines
            ],
        )

        # DS-002 / DS-003: per-line ledger write with delta = -nos.
        # AC-033: V1 does not block negative running_balance (no oversell AC).
        for line in header.lines:
            stock.apply_sale(
                self.session,
                line.design_id,
                line.grade_id,
                payload.sales_date,
                line.nos,
                header.header_id,
                line.line_id,
            )

        # Single-transaction atomicity (header + lines + ledger rows).
        self.session.commit()
        return SalesRead.model_validate(header)

    def list_sales(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        dealer_ids: list[int] | None = None,
        design_ids: list[int] | None = None,
    ) -> list[SalesRead]:
        stmt = select(SalesHeaderModel)
        if date_from is not None:
            stmt = stmt.where(SalesHeaderModel.sales_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(SalesHeaderModel.sales_date <= date_to)
        if dealer_ids:
            stmt = stmt.where(SalesHeaderModel.dealer_id.in_(dealer_ids))
        if design_ids:
            # design_id lives on SalesLineModel — filter headers where any line matches.
            stmt = stmt.where(
                SalesHeaderModel.lines.any(SalesLineModel.design_id.in_(design_ids))
            )
        stmt = stmt.order_by(
            SalesHeaderModel.sales_date.desc(),
            SalesHeaderModel.header_id.desc(),
        )
        headers = self.session.execute(stmt).scalars().unique().all()
        return [SalesRead.model_validate(h) for h in headers]
