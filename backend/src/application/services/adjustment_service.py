from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain import stock
from src.domain.exceptions import ValidationError
from src.infrastructure.db.repositories.master import (
    DesignGradeMapRepository,
    TradingDesignRepository,
)
from src.infrastructure.db.repositories.transactions import AdjustmentHeaderRepository
from src.presentation.schemas.transactions import AdjustmentCreate, AdjustmentRead


class AdjustmentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AdjustmentHeaderRepository(session)
        self.design_repo = TradingDesignRepository(session)
        self.map_repo = DesignGradeMapRepository(session)

    def save_adjustment(self, payload: AdjustmentCreate) -> AdjustmentRead:
        # AC-035 / ERR-010: backstop the Pydantic model_validator (T-046) at service layer
        # so non-HTTP callers also fail fast.
        if payload.stock_date > payload.entry_date:
            raise ValidationError("stock_date must be on or before entry_date")

        # Design must exist + be active.
        design = self.design_repo.get(payload.design_id)
        if not design.is_active:
            raise ValidationError(f"Design {payload.design_id} is inactive")

        # AC-040 / ERR-012: design must have ≥ 1 active (design, grade) mapping.
        active_pairs = self.map_repo.list_active_by_design(payload.design_id)
        if not active_pairs:
            raise ValidationError(
                f"Design {payload.design_id} has no active grade combinations (ERR-012)"
            )
        active_grade_ids = {pair.grade_id for pair in active_pairs}

        # Each line's grade_id must be one of this design's active mappings.
        for line in payload.lines:
            if line.grade_id not in active_grade_ids:
                raise ValidationError(
                    f"Grade {line.grade_id} is not an active mapping for "
                    f"design {payload.design_id}"
                )

        # AC-036: snapshot software_cb per line via closing_balance(stock_date).
        # AC-038: difference = physical_cb - software_cb (signed; no abs()).
        line_payloads: list[dict] = []
        line_diffs: list[tuple[int, int]] = []  # (grade_id, difference)
        for line in payload.lines:
            software_cb = stock.closing_balance(
                self.session,
                payload.design_id,
                line.grade_id,
                payload.stock_date,
            )
            difference = line.physical_cb - software_cb
            line_payloads.append(
                {
                    "grade_id": line.grade_id,
                    "software_cb": software_cb,
                    "physical_cb": line.physical_cb,
                    "difference": difference,
                }
            )
            line_diffs.append((line.grade_id, difference))

        # Persist header + lines in one flush.
        header = self.repo.create_with_lines(
            header_payload={
                "stock_date": payload.stock_date,
                "entry_date": payload.entry_date,
                "design_id": payload.design_id,
                "entered_by_id": payload.entered_by_id,
            },
            line_payloads=line_payloads,
        )

        # AC-039: apply ledger writes with delta=difference, txn_date=stock_date.
        # Sort by line_id (assigned in insert order) to pair line_diffs with persisted_lines
        # deterministically — header.lines via lazy='joined' has no ORDER BY guarantee.
        persisted_lines_sorted = sorted(header.lines, key=lambda l: l.line_id)
        for (grade_id, difference), persisted_line in zip(
            line_diffs, persisted_lines_sorted, strict=True
        ):
            if difference != 0:
                # Zero-difference: audit row in adjustment_line remains; no ledger movement.
                stock.apply_adjustment(
                    self.session,
                    payload.design_id,
                    grade_id,
                    payload.stock_date,
                    difference,
                    header.header_id,
                    persisted_line.line_id,
                )

        self.session.commit()
        return AdjustmentRead.model_validate(header)
