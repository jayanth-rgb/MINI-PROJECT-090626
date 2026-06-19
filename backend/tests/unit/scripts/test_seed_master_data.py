"""Seed-script tests — verifies the 33 PRD rows and idempotency.

Covers: TC-007, TC-011, TC-015, TC-016, TC-022, TC-030.

Idempotency is simulated by calling each seeder twice with a flush in between.
The seeders' existence-check SELECTs do not auto-flush (autoflush=False), so a
manual flush between runs is needed for the second-run dedup to work.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from scripts.seed_master_data import (
    seed_dealers,
    seed_design_grade_map,
    seed_designs,
    seed_grades,
    seed_staff,
    seed_suppliers,
)
from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def _run_twice(session: Session, seeder) -> None:
    seeder(session)
    session.flush()
    seeder(session)
    session.flush()


def test_tc007_seed_suppliers_inserts_3_rows_idempotent(db_session: Session) -> None:
    _run_twice(db_session, seed_suppliers)

    rows = db_session.execute(
        select(SupplierModel).order_by(SupplierModel.supplier_id)
    ).scalars().all()

    assert len(rows) == 3
    expected = [
        ("Manjunatha", "Mallur"),
        ("Dinnesh Reddy", "Mallur"),
        ("Antony Tiles", "Kerala"),
    ]
    actual = [(r.supplier_name, r.place) for r in rows]
    assert actual == expected


def test_tc011_seed_staff_inserts_9_named_rows_idempotent(db_session: Session) -> None:
    _run_twice(db_session, seed_staff)

    rows = db_session.execute(
        select(StaffModel).order_by(StaffModel.staff_id)
    ).scalars().all()

    assert len(rows) == 9
    expected = [
        "Chandran", "Jayapal", "Ramachandraiah", "Sujatha", "Ramya",
        "Vijay", "Sajil", "Ashu", "Amaresh",
    ]
    assert [r.staff_name for r in rows] == expected


def test_tc015_seed_dealers_inserts_3_rows_idempotent(db_session: Session) -> None:
    _run_twice(db_session, seed_dealers)

    rows = db_session.execute(
        select(DealerModel).order_by(DealerModel.dealer_id)
    ).scalars().all()

    assert len(rows) == 3
    expected = [
        ("Raj Hardwares", "Dindivanam"),
        ("Tiles Mart", "Attibelle"),
        ("Shanmugam & Co", "Coimbatore"),
    ]
    assert [(r.dealer_name, r.place) for r in rows] == expected


def test_tc016_seed_grades_inserts_9_codes_idempotent(db_session: Session) -> None:
    _run_twice(db_session, seed_grades)

    rows = db_session.execute(
        select(GradeModel).order_by(GradeModel.grade_id)
    ).scalars().all()

    assert len(rows) == 9
    expected = ["1", "2", "2A", "4", "5", "6", "1OB", "OB", "DIM"]
    assert [r.grade_code for r in rows] == expected


def test_tc022_seed_designs_inserts_3_rows_idempotent(db_session: Session) -> None:
    _run_twice(db_session, seed_designs)

    rows = db_session.execute(
        select(TradingDesignModel).order_by(TradingDesignModel.design_id)
    ).scalars().all()

    assert len(rows) == 3
    expected = [
        ("16X10", "16X10 Ridges"),
        ("12X8", "12X8 Ridges"),
        ("11X7", "11X7 Ridges"),
    ]
    assert [(r.size, r.design_name) for r in rows] == expected


def test_tc030_seed_design_grade_map_inserts_6_pairs_idempotent(
    db_session: Session,
) -> None:
    seed_designs(db_session)
    seed_grades(db_session)
    db_session.flush()

    _run_twice(db_session, seed_design_grade_map)

    rows = db_session.execute(
        select(
            TradingDesignModel.design_name,
            GradeModel.grade_code,
        )
        .join(DesignGradeMapModel, DesignGradeMapModel.design_id == TradingDesignModel.design_id)
        .join(GradeModel, GradeModel.grade_id == DesignGradeMapModel.grade_id)
        .order_by(DesignGradeMapModel.map_id)
    ).all()

    count = db_session.execute(select(func.count(DesignGradeMapModel.map_id))).scalar()
    assert count == 6
    expected = [
        ("16X10 Ridges", "1"),
        ("16X10 Ridges", "2"),
        ("12X8 Ridges", "1"),
        ("12X8 Ridges", "OB"),
        ("11X7 Ridges", "1"),
        ("11X7 Ridges", "2"),
    ]
    assert [(r.design_name, r.grade_code) for r in rows] == expected
