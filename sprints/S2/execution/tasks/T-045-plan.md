# T-045 — `domain.stock` — Stock Ledger arithmetic (HIGHEST RISK in S2)

**Module:** M-003 · **Depends on:** T-043 · **DS:** DS-002, DS-003, DS-004, DS-007

> ⚠ This is the highest-risk file in S2 per HLD R-001 (concurrent-write race) and R-003 (back-dated transactions). 9 critical TCs (TC-079..TC-087). Recommend extra `/ases-critique` attention.

## Implementation logic

```python
# backend/src/domain/stock.py
from __future__ import annotations

from datetime import date, timedelta

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
    # DS-002: acquire SELECT FOR UPDATE on the latest row before reading.
    latest = repo.latest_for_design_grade(design_id, grade_id, for_update=True)
    prior_balance = latest.running_balance if latest is not None else 0
    is_back_dated = latest is not None and txn_date < latest.txn_date

    new_row = repo.insert({
        "design_id": design_id,
        "grade_id": grade_id,
        "txn_date": txn_date,
        "source_type": source_type,
        "source_header_id": source_header_id,
        "source_line_id": source_line_id,
        "delta": delta,
        "running_balance": prior_balance + delta,
    })

    if is_back_dated:
        _recompute_forward(session, design_id, grade_id, txn_date)

    return new_row


def apply_inward(session, design_id, grade_id, date, nos, source_header_id, source_line_id):
    return _apply(session, design_id, grade_id, date, +nos, "inward", source_header_id, source_line_id)


def apply_sale(session, design_id, grade_id, date, nos, source_header_id, source_line_id):
    return _apply(session, design_id, grade_id, date, -nos, "sale", source_header_id, source_line_id)


def apply_adjustment(session, design_id, grade_id, date, difference, source_header_id, source_line_id):
    return _apply(session, design_id, grade_id, date, difference, "adjustment", source_header_id, source_line_id)


def closing_balance(session: Session, design_id: int, grade_id: int, as_of_date: date) -> int:
    repo = StockLedgerRepository(session)
    row = repo.latest_as_of(design_id, grade_id, as_of_date)
    return row.running_balance if row is not None else 0


def opening_balance(session: Session, design_id: int, grade_id: int, month_first_day: date) -> int:
    # DS-004: opening_balance = closing_balance of last day of previous month.
    return closing_balance(session, design_id, grade_id, month_first_day - timedelta(days=1))


def _recompute_forward(
    session: Session,
    design_id: int,
    grade_id: int,
    from_date_inclusive: date,
) -> None:
    """Replay deltas on all rows for (design_id, grade_id) with txn_date >= from_date_inclusive.

    Called only after a back-dated insert. Bounded by AC-021 7-day backdate window per (design,
    grade) → ≤ ~30 rows at realistic throughput per DS-003.
    """
    repo = StockLedgerRepository(session)
    rows = repo.rows_after(design_id, grade_id, from_date_inclusive)
    # rows_after returns ASC by (txn_date, ledger_id) — includes the just-inserted back-dated row.
    running = 0
    # Find the prior running_balance from row immediately before from_date_inclusive.
    prior_row = repo.latest_as_of(design_id, grade_id, from_date_inclusive - timedelta(days=1))
    running = prior_row.running_balance if prior_row is not None else 0
    for r in rows:
        running += r.delta
        r.running_balance = running
    session.flush()
```

## Constraints
- **DS-002 (concurrency):** Every write path goes through `_apply` which calls `latest_for_design_grade(for_update=True)` FIRST. No bypass.
- **DS-003 (materialization + back-date):** `running_balance` is computed once on insert; back-dated insert triggers `_recompute_forward` to replay forward. Window is bounded by the 7-day backdate cap from AC-021 — but the function does NOT enforce the cap (that's the service layer's job per AC-021/028); domain stays pure.
- **DS-004 (carry-forward):** `opening_balance(m_first) = closing_balance(m_first - 1)`. No new ledger row needed; just a function call.
- **DS-007 (layering):** Pure session-in / row-out. No HTTP, no Pydantic, no logging. No global state.
- For `apply_sale`, delta = `-nos` (negative). V1 does NOT block negative `running_balance` — PRD has no oversell prevention; ledger faithfully records reality.
- For `apply_adjustment`, delta = `difference` (caller passes signed value).

## Edge cases the tests will hit
- TC-080 / TC-082: no prior ledger rows → `closing_balance / opening_balance` return 0.
- TC-086: back-dated insert with 2 later rows → forward-recompute replays both.
- TC-087: two concurrent sessions both call `apply_inward(design_id=1, grade_id=1, nos=5)` from balance 0 → second blocks on FOR UPDATE; final state has 2 ledger rows with running_balances [5, 10] (or [5, 10] regardless of which session goes first); no duplicate values.

## Do not touch
Any other file.

## Success criteria
- **Manual:** Load each function; signatures match LLD exactly.
- **Automated:** TC-079..TC-087 all pass.
- **DoD:** 5 public functions; 1 private `_recompute_forward`; no other functions; no module-level state.

## Checkout prompt
*"domain.stock complete — 5 ledger functions with SELECT FOR UPDATE + back-date recompute. HIGHEST RISK file passed."*
