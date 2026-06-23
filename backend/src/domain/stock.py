from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.db.models.transactions import StockLedgerModel
from src.infrastructure.db.repositories.transactions import StockLedgerRepository


def _apply(
    session: Session,
    design_id: int,
    grade_id: int,
    txn_date: date,
    delta: int,
    source_type: str,
    source_header_id: int,
    source_line_id: int,
) -> StockLedgerModel:
    repo = StockLedgerRepository(session)
    # DS-002: serialize concurrent writes per (design, grade) via PG advisory
    # transaction lock BEFORE the FOR UPDATE row lock. Required because
    # `SELECT ... ORDER BY ... LIMIT 1 FOR UPDATE` does NOT re-resolve LIMIT
    # after waiting on a row lock — the second waiter re-reads the same
    # originally-identified row (the now-stale prior latest) instead of the
    # row inserted by the first writer. Discovered by ST-007 (TC-087 functional).
    # The advisory lock key is (design_id, grade_id) packed into pg_advisory_xact_lock's
    # 2-int form; it releases automatically at txn commit/rollback.
    session.execute(
        text("SELECT pg_advisory_xact_lock(:k1, :k2)"),
        {"k1": design_id, "k2": grade_id},
    )
    latest = repo.latest_for_design_grade(design_id, grade_id, for_update=True)
    prior_balance = latest.running_balance if latest is not None else 0
    is_back_dated = latest is not None and txn_date < latest.txn_date

    new_row = repo.insert(
        {
            "design_id": design_id,
            "grade_id": grade_id,
            "txn_date": txn_date,
            "source_type": source_type,
            "source_header_id": source_header_id,
            "source_line_id": source_line_id,
            "delta": delta,
            "running_balance": prior_balance + delta,
        }
    )

    if is_back_dated:
        # DS-003: rewrite running_balance on every later row to incorporate the back-dated delta.
        _recompute_forward(session, design_id, grade_id, txn_date)

    return new_row


def apply_inward(
    session: Session,
    design_id: int,
    grade_id: int,
    date: date,
    nos: int,
    source_header_id: int,
    source_line_id: int,
) -> StockLedgerModel:
    return _apply(
        session,
        design_id,
        grade_id,
        date,
        +nos,
        "inward",
        source_header_id,
        source_line_id,
    )


def apply_sale(
    session: Session,
    design_id: int,
    grade_id: int,
    date: date,
    nos: int,
    source_header_id: int,
    source_line_id: int,
) -> StockLedgerModel:
    # V1: ledger faithfully records reality; PRD has no oversell-prevention AC.
    return _apply(
        session,
        design_id,
        grade_id,
        date,
        -nos,
        "sale",
        source_header_id,
        source_line_id,
    )


def apply_adjustment(
    session: Session,
    design_id: int,
    grade_id: int,
    date: date,
    difference: int,
    source_header_id: int,
    source_line_id: int,
) -> StockLedgerModel:
    return _apply(
        session,
        design_id,
        grade_id,
        date,
        difference,
        "adjustment",
        source_header_id,
        source_line_id,
    )


def closing_balance(
    session: Session,
    design_id: int,
    grade_id: int,
    as_of_date: date,
) -> int:
    repo = StockLedgerRepository(session)
    row = repo.latest_as_of(design_id, grade_id, as_of_date)
    return row.running_balance if row is not None else 0


def opening_balance(
    session: Session,
    design_id: int,
    grade_id: int,
    month_first_day: date,
) -> int:
    # DS-004: opening_balance(m_first) = closing_balance(m_first - 1 day).
    return closing_balance(
        session, design_id, grade_id, month_first_day - timedelta(days=1)
    )


def _recompute_forward(
    session: Session,
    design_id: int,
    grade_id: int,
    from_date_inclusive: date,
) -> None:
    """Replay deltas forward after a back-dated insert.

    Loads rows_after(from_date_inclusive) ASC and rewrites each row's running_balance
    cumulatively, starting from the running_balance of the row immediately before
    from_date_inclusive. Bounded by AC-021's 7-day backdate window per DS-003.
    """
    repo = StockLedgerRepository(session)
    prior_row = repo.latest_as_of(
        design_id, grade_id, from_date_inclusive - timedelta(days=1)
    )
    running = prior_row.running_balance if prior_row is not None else 0
    for row in repo.rows_after(design_id, grade_id, from_date_inclusive):
        running += row.delta
        row.running_balance = running
    session.flush()
