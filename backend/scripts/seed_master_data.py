"""Idempotent seed for the 6 master tables.

Run via:  python -m scripts.seed_master_data
Pre-req:  alembic upgrade head  (creates the 6 master tables from migration 0002)

Rows inserted per AC-003 / AC-006 / AC-009 / AC-010 / AC-014 / AC-018:
  3 suppliers + 9 staff + 3 dealers + 9 grades + 3 designs + 6 design-grade pairs = 33
Re-running this script must insert 0 new rows.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.session import SessionLocal

SUPPLIERS = [
    {"supplier_name": "Manjunatha", "place": "Mallur"},
    {"supplier_name": "Dinnesh Reddy", "place": "Mallur"},
    {"supplier_name": "Antony Tiles", "place": "Kerala"},
]

STAFF = [
    "Chandran",
    "Jayapal",
    "Ramachandraiah",
    "Sujatha",
    "Ramya",
    "Vijay",
    "Sajil",
    "Ashu",
    "Amaresh",
]

DEALERS = [
    {"dealer_name": "Raj Hardwares", "place": "Dindivanam"},
    {"dealer_name": "Tiles Mart", "place": "Attibelle"},
    {"dealer_name": "Shanmugam & Co", "place": "Coimbatore"},
]

GRADE_CODES = ["1", "2", "2A", "4", "5", "6", "1OB", "OB", "DIM"]

DESIGNS = [
    {"size": "16X10", "design_name": "16X10 Ridges"},
    {"size": "12X8", "design_name": "12X8 Ridges"},
    {"size": "11X7", "design_name": "11X7 Ridges"},
]

DESIGN_GRADE_PAIRS = [
    ("16X10 Ridges", "1"),
    ("16X10 Ridges", "2"),
    ("12X8 Ridges", "1"),
    ("12X8 Ridges", "OB"),
    ("11X7 Ridges", "1"),
    ("11X7 Ridges", "2"),
]


def seed_suppliers(session: Session) -> None:
    for row in SUPPLIERS:
        exists = session.execute(
            select(SupplierModel).where(
                SupplierModel.supplier_name == row["supplier_name"],
                SupplierModel.place == row["place"],
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(SupplierModel(**row))


def seed_staff(session: Session) -> None:
    for name in STAFF:
        exists = session.execute(
            select(StaffModel).where(StaffModel.staff_name == name)
        ).scalar_one_or_none()
        if exists is None:
            session.add(StaffModel(staff_name=name))


def seed_dealers(session: Session) -> None:
    for row in DEALERS:
        exists = session.execute(
            select(DealerModel).where(
                DealerModel.dealer_name == row["dealer_name"],
                DealerModel.place == row["place"],
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(DealerModel(**row))


def seed_grades(session: Session) -> None:
    for code in GRADE_CODES:
        exists = session.execute(
            select(GradeModel).where(GradeModel.grade_code == code)
        ).scalar_one_or_none()
        if exists is None:
            session.add(GradeModel(grade_code=code))


def seed_designs(session: Session) -> None:
    for row in DESIGNS:
        exists = session.execute(
            select(TradingDesignModel).where(
                TradingDesignModel.size == row["size"],
                TradingDesignModel.design_name == row["design_name"],
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(TradingDesignModel(**row))


def seed_design_grade_map(session: Session) -> None:
    # Materialize prior INSERTs so design.design_id and grade.grade_id are assigned.
    session.flush()
    for design_name, grade_code in DESIGN_GRADE_PAIRS:
        design = session.execute(
            select(TradingDesignModel).where(
                TradingDesignModel.design_name == design_name
            )
        ).scalar_one()
        grade = session.execute(
            select(GradeModel).where(GradeModel.grade_code == grade_code)
        ).scalar_one()
        exists = session.execute(
            select(DesignGradeMapModel).where(
                DesignGradeMapModel.design_id == design.design_id,
                DesignGradeMapModel.grade_id == grade.grade_id,
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                DesignGradeMapModel(
                    design_id=design.design_id,
                    grade_id=grade.grade_id,
                )
            )


def main() -> None:
    session = SessionLocal()
    try:
        seed_suppliers(session)
        seed_staff(session)
        seed_dealers(session)
        seed_grades(session)
        seed_designs(session)
        seed_design_grade_map(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
