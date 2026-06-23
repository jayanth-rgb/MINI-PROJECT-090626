"""IS-008 — Back-dated inward triggers domain._recompute_forward across all later rows.

DS-003 / HLD R-003 mitigation verification end-to-end.
"""
from __future__ import annotations

from datetime import date

from src.domain import stock
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def test_is008(db_session):
    design = TradingDesignModel(size="16X10", design_name="16X10 Ridges")
    grade = GradeModel(grade_code="1")
    db_session.add_all([design, grade])
    db_session.flush()
    db_session.add(
        DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
    )
    db_session.commit()

    # Forward sequence: Jun 22 +30 → balance 30 ; Jun 25 +20 → balance 50
    stock.apply_inward(
        db_session, design.design_id, grade.grade_id, date(2026, 6, 22), 30, 1, 1
    )
    stock.apply_inward(
        db_session, design.design_id, grade.grade_id, date(2026, 6, 25), 20, 2, 1
    )
    db_session.commit()

    # Back-date insert: Jun 20 +5
    stock.apply_inward(
        db_session, design.design_id, grade.grade_id, date(2026, 6, 20), 5, 3, 1
    )
    db_session.commit()

    rows = (
        db_session.query(StockLedgerModel)
        .filter_by(design_id=design.design_id, grade_id=grade.grade_id)
        .order_by(
            StockLedgerModel.txn_date.asc(),
            StockLedgerModel.ledger_id.asc(),
        )
        .all()
    )
    assert len(rows) == 3
    # Cumulative replay starting from prior_balance=0 (no rows before Jun 20):
    # C(Jun 20, Δ=+5) → 5; A(Jun 22, Δ=+30) → 35; B(Jun 25, Δ=+20) → 55
    balances = [row.running_balance for row in rows]
    assert balances == [5, 35, 55], f"_recompute_forward broken: got {balances}"

    # Deltas unchanged by recompute
    deltas = [row.delta for row in rows]
    assert deltas == [5, 30, 20]

    # Source types preserved
    source_types = [row.source_type for row in rows]
    assert source_types == ["inward", "inward", "inward"]
