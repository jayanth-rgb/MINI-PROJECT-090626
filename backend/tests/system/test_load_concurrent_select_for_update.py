"""ST-007 — TC-087 functional: two concurrent sessions serialize via SELECT FOR UPDATE.

HLD R-001 mitigation verification with real 2-session concurrency. Uses the
session-scoped pg_container engine to spawn two independent sessions and runs
apply_inward in parallel threads against the SAME (design, grade).
"""
from __future__ import annotations

import threading
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.domain import stock
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import StockLedgerModel


def test_st007_two_concurrent_apply_inward_serialize(pg_container):
    """Two threads each call apply_inward(nos=5) starting from balance=10.

    Expected: SELECT FOR UPDATE serializes the second thread until the first
    commits. Final state has 3 rows with monotonically-increasing running_balance:
    seed=10, first=15, second=20 (or 20, 15 depending on which thread won
    the lock — but both increments must be visible).
    """
    engine = pg_container._engine
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    # Seed in a setup session
    with SessionLocal() as setup_session:
        design = TradingDesignModel(size="16X10", design_name="Concurrent")
        grade = GradeModel(grade_code="C")
        setup_session.add_all([design, grade])
        setup_session.flush()
        setup_session.add(
            DesignGradeMapModel(
                design_id=design.design_id, grade_id=grade.grade_id
            )
        )
        # Seed running_balance = 10 via direct apply_inward
        stock.apply_inward(
            setup_session,
            design.design_id,
            grade.grade_id,
            date(2026, 6, 1),
            10,
            1,
            1,
        )
        setup_session.commit()
        design_id = design.design_id
        grade_id = grade.grade_id

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(source_header_id: int):
        try:
            with SessionLocal() as session:
                barrier.wait(timeout=10)  # both threads start the apply call together
                stock.apply_inward(
                    session,
                    design_id,
                    grade_id,
                    date(2026, 6, 2),
                    5,
                    source_header_id,
                    1,
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=(2,))
    t2 = threading.Thread(target=worker, args=(3,))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert not errors, f"Worker threads errored: {errors}"

    # Verify final state via fresh session
    try:
        with SessionLocal() as verify_session:
            rows = (
                verify_session.query(StockLedgerModel)
                .filter_by(design_id=design_id, grade_id=grade_id)
                .order_by(
                    StockLedgerModel.txn_date.asc(),
                    StockLedgerModel.ledger_id.asc(),
                )
                .all()
            )
            # 1 seed + 2 worker inserts
            assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}: {[r.running_balance for r in rows]}"
            balances = [r.running_balance for r in rows]
            # Seed=10; both workers added +5 each; final last row must be 20
            assert balances[0] == 10, f"Seed row balance wrong: {balances}"
            # The 2 worker rows (positions [1], [2]) must be 15 and 20 in some order
            # — if SELECT FOR UPDATE serialized correctly, second won't read stale 10
            assert sorted(balances[1:]) == [15, 20], (
                f"Race detected: expected [15, 20], got {sorted(balances[1:])}. "
                "If both are 15, the lock didn't serialize."
            )
    finally:
        # CRITICAL: this test commits OUTSIDE the rollback-only db_session fixture,
        # so without explicit cleanup the rows persist in the session-scoped
        # testcontainer DB and pollute later tests (e.g. unit/scripts/seed tests
        # that assert exact row counts). Clean up the ledger + map + grade + design.
        with SessionLocal() as cleanup_session:
            cleanup_session.execute(
                text(
                    "DELETE FROM tbl_stock_ledger "
                    "WHERE design_id = :d AND grade_id = :g"
                ),
                {"d": design_id, "g": grade_id},
            )
            cleanup_session.execute(
                text(
                    "DELETE FROM tbl_design_grade_map "
                    "WHERE design_id = :d AND grade_id = :g"
                ),
                {"d": design_id, "g": grade_id},
            )
            cleanup_session.execute(
                text("DELETE FROM tbl_grade_master WHERE grade_id = :g"),
                {"g": grade_id},
            )
            cleanup_session.execute(
                text("DELETE FROM tbl_trading_design_master WHERE design_id = :d"),
                {"d": design_id},
            )
            cleanup_session.commit()
