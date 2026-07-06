"""V2 TC-195, TC-196, TC-197 — InwardReportService integration tests.

Verifies the DS-017 reconciliation invariant, filter behaviour, and ordering
against a real PostgreSQL via the shared db_session fixture.
"""
from __future__ import annotations

from datetime import date

from src.application.services.inward_report_service import InwardReportService
from src.infrastructure.db.models.master import (
    GradeModel,
    SupplierModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    InwardHeaderModel,
    InwardLineModel,
)

from tests.integration.v2._helpers import seed_staff


def _seed_masters_for_inward(
    session,
    designs: list[tuple[int, str, str]],
    grades: list[tuple[int, str]],
    suppliers: list[tuple[int, str, str]],
) -> None:
    for did, size, name in designs:
        session.add(TradingDesignModel(design_id=did, size=size, design_name=name))
    for gid, code in grades:
        session.add(GradeModel(grade_id=gid, grade_code=code))
    for sid, name, place in suppliers:
        session.add(SupplierModel(supplier_id=sid, supplier_name=name, place=place))
    session.flush()


def _seed_inward_row(
    session,
    header_id: int,
    purchase_date: date,
    supplier_id: int,
    place: str,
    design_id: int,
    grade_id: int,
    nos: int,
) -> None:
    session.add(
        InwardHeaderModel(
            header_id=header_id,
            purchase_date=purchase_date,
            supplier_id=supplier_id,
            place=place,
            entered_by_id=1,
        )
    )
    session.flush()
    session.add(
        InwardLineModel(
            header_id=header_id,
            design_id=design_id,
            grade_id=grade_id,
            nos=nos,
        )
    )
    session.flush()


def test_tc195_generate_no_filters_reconciliation_holds(db_session):
    _seed_masters_for_inward(
        db_session,
        designs=[(1, "16X10", "16X10 Ridges"), (2, "12X8", "12X8 Ridges")],
        grades=[(1, "1"), (2, "2")],
        suppliers=[(1, "Manjunatha", "Mallur"), (2, "Kerala Co", "Kerala")],
    )
    seed_staff(db_session)
    _seed_inward_row(db_session, 1, date(2026, 7, 1), 1, "Mallur", 1, 1, 100)
    _seed_inward_row(db_session, 2, date(2026, 7, 1), 1, "Mallur", 1, 2, 50)
    _seed_inward_row(db_session, 3, date(2026, 7, 2), 2, "Kerala", 2, 1, 75)

    resp = InwardReportService(db_session).generate()

    sum_txn_nos = sum(r.nos for r in resp.transactions)
    sum_consol_nos = sum(r.total_nos for r in resp.consolidation)
    assert sum_txn_nos == 225
    assert sum_consol_nos == 225
    assert sum_txn_nos == sum_consol_nos
    assert len(resp.transactions) == 3
    assert len(resp.consolidation) == 3


def test_tc196_generate_with_date_filter_narrows_both_sections(db_session):
    _seed_masters_for_inward(
        db_session,
        designs=[(1, "16X10", "16X10 Ridges"), (2, "12X8", "12X8 Ridges")],
        grades=[(1, "1")],
        suppliers=[(1, "Manjunatha", "Mallur"), (2, "Kerala Co", "Kerala")],
    )
    seed_staff(db_session)
    _seed_inward_row(db_session, 1, date(2026, 7, 1), 1, "Mallur", 1, 1, 100)
    _seed_inward_row(db_session, 2, date(2026, 7, 2), 2, "Kerala", 2, 1, 75)

    resp = InwardReportService(db_session).generate(
        date_from=date(2026, 7, 2),
        date_to=date(2026, 7, 2),
    )
    assert len(resp.transactions) == 1
    assert resp.transactions[0].nos == 75
    assert resp.consolidation[0].total_nos == 75
    assert sum(r.nos for r in resp.transactions) == sum(
        r.total_nos for r in resp.consolidation
    )


def test_tc197_generate_orders_consolidation_by_design_name_and_transactions_by_date(
    db_session,
):
    _seed_masters_for_inward(
        db_session,
        designs=[(1, "16X10", "16X10 Ridges"), (2, "12X8", "12X8 Ridges")],
        grades=[(1, "1")],
        suppliers=[(1, "Manjunatha", "Mallur")],
    )
    seed_staff(db_session)
    _seed_inward_row(db_session, 1, date(2026, 7, 2), 1, "Mallur", 2, 1, 30)
    _seed_inward_row(db_session, 2, date(2026, 7, 1), 1, "Mallur", 1, 1, 100)

    resp = InwardReportService(db_session).generate()

    assert resp.consolidation[0].design_name == "12X8 Ridges"
    assert resp.consolidation[1].design_name == "16X10 Ridges"
    assert resp.transactions[0].purchase_date == date(2026, 7, 1)
    assert resp.transactions[1].purchase_date == date(2026, 7, 2)
