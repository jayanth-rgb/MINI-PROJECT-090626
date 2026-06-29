"""TC-153, TC-154, TC-155 — F-012 Carry-forward end-to-end verification.

Verifies FORMULA-002 (opening_balance = closing_balance of prior month last day)
against the EXISTING domain.stock primitives from S2. No new code paths.

Uses db_session fixture (testcontainers PG) + domain.stock.apply_inward/apply_sale
+ domain.stock.opening_balance/closing_balance.
"""
from __future__ import annotations

from datetime import date

from src.domain import stock
from src.domain.stock import closing_balance, opening_balance
from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


# ---------------------------------------------------------------------------
# In-file seed helpers
# ---------------------------------------------------------------------------


def _seed_masters(db, design_name="16X10 Ridges", size="16X10", grade_code="1"):
    d = TradingDesignModel(design_name=design_name, size=size, is_active=True)
    g = GradeModel(grade_code=grade_code, is_active=True)
    db.add_all([d, g])
    db.flush()
    db.add(DesignGradeMapModel(design_id=d.design_id, grade_id=g.grade_id, is_active=True))
    db.flush()
    return d.design_id, g.grade_id


# ---------------------------------------------------------------------------
# TC-153 — opening_balance(June 1) == closing_balance(May 31) (FORMULA-002)
# ---------------------------------------------------------------------------


def test_tc153_opening_balance_equals_prior_month_closing(db_session):
    """TC-153: FORMULA-002 end-to-end — opening(N+1 month first) == closing(N month last day).

    May transactions → May 31 closing = 50.
    June 1 opening must equal 50 before any June transaction.
    After applying a June 3 inward of 10, running_balance must be 60.
    """
    design_id, grade_id = _seed_masters(db_session)

    # Month N (May 2026) transactions
    stock.apply_inward(db_session, design_id, grade_id, date(2026, 5, 10), 80, 1, 1)
    stock.apply_sale(db_session, design_id, grade_id, date(2026, 5, 25), 30, 1, 2)
    db_session.commit()

    # May 31 closing should be 50 (80 - 30)
    cb_may_31 = closing_balance(db_session, design_id, grade_id, date(2026, 5, 31))
    assert cb_may_31 == 50, f"Expected May 31 closing=50, got {cb_may_31}"

    # June 1 opening must equal May 31 closing
    ob_june_1 = opening_balance(db_session, design_id, grade_id, date(2026, 6, 1))
    assert ob_june_1 == 50, f"Expected June 1 opening=50, got {ob_june_1}"

    # First June transaction: inward of 10 → running_balance should be 60
    row = stock.apply_inward(db_session, design_id, grade_id, date(2026, 6, 3), 10, 2, 1)
    db_session.commit()
    assert row.running_balance == 60, f"Expected running_balance=60, got {row.running_balance}"


# ---------------------------------------------------------------------------
# TC-154 — opening = 0 for never-touched pair (RULE-012)
# ---------------------------------------------------------------------------


def test_tc154_opening_balance_zero_for_new_pair(db_session):
    """TC-154: No prior ledger rows → opening_balance = 0, closing_balance = 0.

    Uses design_id=99 + grade_id=99 via distinct seeds — never any ledger rows.
    """
    # Seed a design and grade that will never have any transactions
    d = TradingDesignModel(design_name="Never Touched Design", size="99X99", is_active=True)
    g = GradeModel(grade_code="ZZ", is_active=True)
    db_session.add_all([d, g])
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=d.design_id, grade_id=g.grade_id, is_active=True))
    db_session.flush()

    ob = opening_balance(db_session, d.design_id, g.grade_id, date(2026, 6, 1))
    cb = closing_balance(db_session, d.design_id, g.grade_id, date(2026, 6, 15))
    assert ob == 0, f"Expected opening=0, got {ob}"
    assert cb == 0, f"Expected closing=0, got {cb}"


# ---------------------------------------------------------------------------
# TC-155 — Back-dated cross-month insert → carry-forward correct
# ---------------------------------------------------------------------------


def test_tc155_backdated_crossmonth_insert_carry_forward_correct(db_session):
    """TC-155: Back-dated May 30 row (inserted on June 4, within 7-day window) must
    leave May 31 closing AND June 1 opening both reflecting both rows (recompute_forward).

    Step 1: Insert May 28 inward of 40 → running_balance=40.
    Step 2: Back-date May 30 inward of 25 (inserted June 4) → recompute_forward runs.
    After step 2: May 31 closing=65, June 1 opening=65.
    """
    design_id, grade_id = _seed_masters(db_session)

    # Step 1: May 28 inward
    stock.apply_inward(db_session, design_id, grade_id, date(2026, 5, 28), 40, 1, 1)
    db_session.commit()

    cb_after_step1 = closing_balance(db_session, design_id, grade_id, date(2026, 5, 31))
    assert cb_after_step1 == 40, f"After step 1, expected May 31 closing=40, got {cb_after_step1}"

    # Step 2: Back-dated May 30 inward of 25 (back-dated 5 days, within 7-day window)
    # domain.stock._apply detects is_back_dated and calls _recompute_forward
    stock.apply_inward(db_session, design_id, grade_id, date(2026, 5, 30), 25, 2, 1)
    db_session.commit()

    cb_may_31 = closing_balance(db_session, design_id, grade_id, date(2026, 5, 31))
    ob_june_1 = opening_balance(db_session, design_id, grade_id, date(2026, 6, 1))

    assert cb_may_31 == 65, f"Expected May 31 closing=65 after backdate, got {cb_may_31}"
    assert ob_june_1 == 65, f"Expected June 1 opening=65 after backdate, got {ob_june_1}"
