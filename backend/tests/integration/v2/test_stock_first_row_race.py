"""V2 TC-207 — first-row insert race regression (TD-008 / DS-015 advisory lock).

Two concurrent threads call domain.stock._apply on an empty ledger for the same
(design_id, grade_id). pg_advisory_xact_lock (DS-002/DS-015) must serialize the
writes so exactly one row per delta is created and running_balance carries
forward correctly — no IntegrityError, no duplicate-key errors.

This test intentionally uses its own SessionLocal (not the rollback-only
db_session fixture) because both workers need to commit for the second one to
observe the first's row via SELECT FOR UPDATE. Explicit cleanup at the end
keeps the session-scoped container clean for later tests.
"""
from __future__ import annotations

import threading
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from src.domain import stock
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    InwardHeaderModel,
    InwardLineModel,
    StockLedgerModel,
)


def test_tc207_two_concurrent_first_row_inserts_serialize_via_advisory_lock(pg_container):
    engine = pg_container._engine
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    # Setup: masters + two inward headers so both threads have a valid
    # (source_header_id, source_line_id) pair to reference. Ledger table is
    # empty for (design_id, grade_id) — this is the "first row insert" case.
    with SessionLocal() as setup:
        design = TradingDesignModel(size="16X10", design_name="TC207 Design")
        grade = GradeModel(grade_code="TC207")
        supplier = SupplierModel(supplier_name="TC207 Supplier", place="Somewhere")
        staff = StaffModel(staff_name="TC207 Staff")
        setup.add_all([design, grade, supplier, staff])
        setup.flush()
        setup.add(
            DesignGradeMapModel(design_id=design.design_id, grade_id=grade.grade_id)
        )
        # Two inward headers/lines — one per worker — to satisfy source FK ints.
        h1 = InwardHeaderModel(
            purchase_date=date(2026, 7, 2),
            supplier_id=supplier.supplier_id,
            place="Somewhere",
            entered_by_id=staff.staff_id,
        )
        h2 = InwardHeaderModel(
            purchase_date=date(2026, 7, 2),
            supplier_id=supplier.supplier_id,
            place="Somewhere",
            entered_by_id=staff.staff_id,
        )
        setup.add_all([h1, h2])
        setup.flush()
        l1 = InwardLineModel(
            header_id=h1.header_id, design_id=design.design_id, grade_id=grade.grade_id, nos=50
        )
        l2 = InwardLineModel(
            header_id=h2.header_id, design_id=design.design_id, grade_id=grade.grade_id, nos=30
        )
        setup.add_all([l1, l2])
        setup.flush()
        setup.commit()
        design_id = design.design_id
        grade_id = grade.grade_id
        h1_id, l1_id = h1.header_id, l1.line_id
        h2_id, l2_id = h2.header_id, l2.line_id

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(delta: int, header_id: int, line_id: int) -> None:
        try:
            with SessionLocal() as session:
                barrier.wait(timeout=10)
                stock.apply_inward(
                    session,
                    design_id,
                    grade_id,
                    date(2026, 7, 2),
                    delta,
                    header_id,
                    line_id,
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=(50, h1_id, l1_id))
    t2 = threading.Thread(target=worker, args=(30, h2_id, l2_id))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    try:
        assert not errors, f"Concurrent first-row inserts errored: {errors}"

        with SessionLocal() as verify:
            rows = (
                verify.query(StockLedgerModel)
                .filter_by(design_id=design_id, grade_id=grade_id)
                .order_by(StockLedgerModel.ledger_id.asc())
                .all()
            )
            assert len(rows) == 2, (
                f"Expected 2 ledger rows (one per worker), got {len(rows)}"
            )
            balances = [r.running_balance for r in rows]
            # Whichever worker acquired the advisory lock first inserted its
            # delta on top of balance 0; the second saw balance = first_delta.
            # Final row's running_balance must be the cumulative sum (80).
            assert balances[-1] == 80, (
                f"final running_balance {balances[-1]} != 80 — race detected"
            )
            assert set(balances) == {50, 80} or set(balances) == {30, 80}, (
                f"Intermediate balances wrong: {balances}"
            )
    finally:
        with SessionLocal() as cleanup:
            cleanup.execute(
                text("DELETE FROM tbl_stock_ledger WHERE design_id = :d AND grade_id = :g"),
                {"d": design_id, "g": grade_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_inward_line WHERE design_id = :d AND grade_id = :g"),
                {"d": design_id, "g": grade_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_inward_header WHERE header_id IN (:h1, :h2)"),
                {"h1": h1_id, "h2": h2_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_design_grade_map WHERE design_id = :d AND grade_id = :g"),
                {"d": design_id, "g": grade_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_grade_master WHERE grade_id = :g"),
                {"g": grade_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_trading_design_master WHERE design_id = :d"),
                {"d": design_id},
            )
            cleanup.execute(
                text("DELETE FROM tbl_staff_master WHERE staff_id NOT IN (SELECT DISTINCT entered_by_id FROM tbl_inward_header)")
            )
            cleanup.execute(
                text("DELETE FROM tbl_supplier_master WHERE supplier_id NOT IN (SELECT DISTINCT supplier_id FROM tbl_inward_header)")
            )
            cleanup.commit()
