"""TC-143, TC-144, TC-145, TC-146 — SalesReportService unit + edge tests (F-011).

Co-located edge tests per project convention (no separate _edge.py file).
All tests are deterministic: fixed dates, no datetime.now(), no uuid4().
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.application.services.sales_report_service import SalesReportService
from src.infrastructure.db.models.master import (
    DealerModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.models.transactions import (
    SalesHeaderModel,
    SalesLineModel,
)
from src.presentation.schemas.sales_report import (
    ConsolidationRow,
    SalesReportResponse,
    TransactionRow,
)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_staff(db):
    """Seed minimal loader + verifier staff (required FK on SalesHeaderModel)."""
    from src.infrastructure.db.models.master import StaffModel
    loader = StaffModel(staff_name="Loader A")
    verifier = StaffModel(staff_name="Verifier B")
    db.add_all([loader, verifier])
    db.flush()
    return loader.staff_id, verifier.staff_id


def _seed_dealer(db, name: str, place: str) -> DealerModel:
    d = DealerModel(dealer_name=name, place=place, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_design(db, name: str, size: str) -> TradingDesignModel:
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, code: str) -> GradeModel:
    g = GradeModel(grade_code=code, is_active=True)
    db.add(g)
    db.flush()
    return g


def _seed_sale(db, sales_date, dealer_id, place_snapshot, loader_id, verifier_id, lines):
    """lines: list of dicts {design_id, grade_id, nos}"""
    header = SalesHeaderModel(
        sales_date=sales_date,
        dealer_id=dealer_id,
        place=place_snapshot,
        loading_staff_id=loader_id,
        verified_by_id=verifier_id,
    )
    db.add(header)
    db.flush()
    for ln in lines:
        sl = SalesLineModel(
            header_id=header.header_id,
            design_id=ln["design_id"],
            grade_id=ln["grade_id"],
            nos=ln["nos"],
        )
        db.add(sl)
    db.flush()
    return header


# ---------------------------------------------------------------------------
# TC-143: all-None filters produce an empty filter list (no WHERE predicates)
# ---------------------------------------------------------------------------

def test_tc143_all_none_filters_produce_empty_filter_list(db_session):
    """SalesReportService._build_filters with all-None inputs returns an empty list.

    Verifies RULE-018: no filters means full dataset — both queries run without
    optional WHERE predicates.
    """
    svc = SalesReportService(db_session)
    filters = svc._build_filters(
        date_from=None,
        date_to=None,
        dealer_ids=None,
        places=None,
        design_ids=None,
    )
    assert isinstance(filters, list), "Expected list from _build_filters"
    assert len(filters) == 0, (
        f"Expected 0 filter predicates for all-None inputs, got {len(filters)}"
    )


# ---------------------------------------------------------------------------
# TC-144 (edge): empty list [] filters are treated as no filter (falsy guard)
# ---------------------------------------------------------------------------

def test_tc144_empty_list_filters_treated_as_no_filter(db_session):
    """Edge — dealer_ids=[] is falsy and must NOT produce a dealer_id IN () predicate.

    Verifies the 'if dealer_ids:' guard. An empty IN () would return zero rows;
    skipping is the correct behaviour (same result as passing None).
    """
    svc = SalesReportService(db_session)

    # Seed one sale to verify full dataset is returned under both calls
    loader_id, verifier_id = _seed_staff(db_session)
    dealer = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade = _seed_grade(db_session, "1")
    _seed_sale(
        db_session,
        date(2026, 6, 15),
        dealer.dealer_id,
        "Dindivanam",
        loader_id,
        verifier_id,
        [{"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 5}],
    )

    # Call with empty list dealer_ids
    result_empty_list = svc.generate(dealer_ids=[])
    # Call with None dealer_ids — both must return identical row counts
    result_none = svc.generate(dealer_ids=None)

    assert len(result_empty_list.transactions) == len(result_none.transactions), (
        "dealer_ids=[] must behave identically to dealer_ids=None (no filter)"
    )
    assert len(result_empty_list.transactions) == 1, (
        "Expected 1 transaction row (the seeded sale)"
    )

    # Verify _build_filters also returns 0 for empty list
    filters_empty = svc._build_filters(
        date_from=None, date_to=None, dealer_ids=[], places=[], design_ids=[]
    )
    assert len(filters_empty) == 0, (
        f"Expected 0 predicates for all-empty-list inputs, got {len(filters_empty)}"
    )


# ---------------------------------------------------------------------------
# TC-145 (edge): divergent sums raise AssertionError with "AC-050" message
# ---------------------------------------------------------------------------

def test_tc145_divergent_sums_raise_assertion_error(db_session):
    """Edge — AC-050 defense-in-depth: divergent consolidation/transactions sums
    must raise AssertionError containing 'AC-050'.

    Uses MagicMock to inject a session whose execute() returns controlled results
    that deliberately diverge between the consolidation and transactions queries.
    """
    # We mock the SalesReportService's session.execute to return divergent sums.
    # Strategy: patch _query_consolidation and _query_transactions independently
    # so consolidation total != transactions total.
    svc = SalesReportService(db_session)

    # Build fake rows with non-matching totals
    fake_consolidation = [
        ConsolidationRow(
            design_id=1,
            design_name="16X10 Ridges",
            size="16X10",
            grade_id=1,
            grade_code="1",
            total_nos=100,  # consolidation sum = 100
        )
    ]
    fake_transactions = [
        TransactionRow(
            sales_date=date(2026, 6, 15),
            dealer_id=1,
            dealer_name="Raj Hardwares",
            place="Dindivanam",
            design_id=1,
            design_name="16X10 Ridges",
            size="16X10",
            grade_id=1,
            grade_code="1",
            nos=99,  # transactions sum = 99 — deliberately divergent
        )
    ]

    with (
        patch.object(SalesReportService, "_query_consolidation", return_value=fake_consolidation),
        patch.object(SalesReportService, "_query_transactions", return_value=fake_transactions),
    ):
        with pytest.raises(AssertionError) as exc_info:
            svc.generate()

    assert "AC-050" in str(exc_info.value), (
        f"Expected 'AC-050' in AssertionError message, got: {exc_info.value}"
    )


# ---------------------------------------------------------------------------
# TC-146: consolidation rows include all GROUP BY columns + total_nos
# ---------------------------------------------------------------------------

def test_tc146_consolidation_row_has_all_columns(db_session):
    """SalesReportService.generate consolidation rows expose all GROUP BY columns.

    Verifies: design_id, design_name, size, grade_id, grade_code, total_nos.
    Single seed row: dealer_id=1, design='16X10 Ridges', grade='1', nos=7.
    """
    loader_id, verifier_id = _seed_staff(db_session)
    dealer = _seed_dealer(db_session, "Raj Hardwares", "Dindivanam")
    design = _seed_design(db_session, "16X10 Ridges", "16X10")
    grade = _seed_grade(db_session, "1")
    _seed_sale(
        db_session,
        date(2026, 6, 5),
        dealer.dealer_id,
        "Dindivanam",
        loader_id,
        verifier_id,
        [{"design_id": design.design_id, "grade_id": grade.grade_id, "nos": 7}],
    )

    svc = SalesReportService(db_session)
    result = svc.generate()

    assert len(result.consolidation) == 1, (
        f"Expected 1 consolidation row, got {len(result.consolidation)}"
    )
    row = result.consolidation[0]

    # All GROUP BY columns must be present and correct
    assert row.design_id == design.design_id
    assert row.design_name == "16X10 Ridges"
    assert row.size == "16X10"
    assert row.grade_id == grade.grade_id
    assert row.grade_code == "1"
    assert row.total_nos == 7, f"Expected total_nos=7, got {row.total_nos}"
