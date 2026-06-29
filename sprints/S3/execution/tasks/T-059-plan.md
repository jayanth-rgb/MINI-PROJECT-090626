# T-059 — `infrastructure/db/repositories/ledger_aggregates.py` — single-query aggregator

**Module:** M-004 · **Depends on:** — (Group A) · **DS:** DS-016

## Context anchor
Reads from S2 `models/transactions.py` (StockLedgerModel + `ix_stock_ledger_dgt` composite index at line 255). Inherits the `BaseRepository[T]` contract from S1 `repositories/base.py`. Sibling to (but does not modify) S1 `repositories/master.py` and S2 `repositories/transactions.py`.

The dashboard requires monthly `inward / outward / adjust` SUMs per `(design, grade)`. **DS-016** mandates a **single GROUP BY** query rather than per-pair sub-queries — the planner uses the `(design_id, grade_id)` prefix of `ix_stock_ledger_dgt` plus the `txn_date` range to scan in-window rows once.

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/ledger_aggregates.py
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.engine import Row

from src.infrastructure.db.models.transactions import StockLedgerModel
from src.infrastructure.db.repositories.base import BaseRepository


class LedgerAggregatesRepository(BaseRepository[StockLedgerModel]):
    """Read-only aggregator over tbl_stock_ledger for dashboard monthly totals (DS-016)."""

    def sum_deltas_by_source_type(
        self,
        month_start: date,
        as_of_date: date,
    ) -> list[Row]:
        """Return one Row per (design_id, grade_id) with CASE-aggregated SUMs of:
          - inward_sum:  SUM(delta)  WHERE source_type = 'inward'
          - outward_sum: SUM(-delta) WHERE source_type = 'sale'      (inverted so column reads positive)
          - adjust_sum:  SUM(delta)  WHERE source_type = 'adjustment'

        Window: txn_date BETWEEN :month_start AND :as_of_date (inclusive both ends).
        Index: ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC) supports
        the GROUP BY prefix + the date-range scan.
        """
        stmt = (
            select(
                StockLedgerModel.design_id.label("design_id"),
                StockLedgerModel.grade_id.label("grade_id"),
                func.coalesce(
                    func.sum(
                        case((StockLedgerModel.source_type == "inward", StockLedgerModel.delta), else_=0)
                    ),
                    0,
                ).label("inward_sum"),
                func.coalesce(
                    func.sum(
                        case((StockLedgerModel.source_type == "sale", -StockLedgerModel.delta), else_=0)
                    ),
                    0,
                ).label("outward_sum"),
                func.coalesce(
                    func.sum(
                        case((StockLedgerModel.source_type == "adjustment", StockLedgerModel.delta), else_=0)
                    ),
                    0,
                ).label("adjust_sum"),
            )
            .where(StockLedgerModel.txn_date.between(month_start, as_of_date))
            .group_by(StockLedgerModel.design_id, StockLedgerModel.grade_id)
        )
        return list(self.session.execute(stmt).all())
```

## Constraints
- **Single SQL statement.** No N+1, no Python-side aggregation. Per DS-016.
- `outward_sum` must read **positive** in the projection (the ledger stores sales as negative deltas; the SUM negates them).
- `func.coalesce(..., 0)` so missing `(design, grade)` pairs return 0 rather than NULL.
- `between(start, end)` is inclusive on both ends — matches AC-053 / AC-052 month-window semantics.
- Repository inherits `BaseRepository[StockLedgerModel]` — `self.session` is provided by the base.
- Returns raw `Row` objects so `DashboardService` can read columns by label (`row.inward_sum`, etc.) and merge with master data efficiently.

## Do not touch
- `backend/src/infrastructure/db/repositories/base.py`
- `backend/src/infrastructure/db/repositories/master.py` (modified separately in T-060)
- `backend/src/infrastructure/db/repositories/transactions.py`
- Any model file
- Any test file

## Success criteria
- **Manual**: with seeded ledger data (1 design × 2 grades × mixed inward/sale/adjustment rows across June 2026), call `sum_deltas_by_source_type(date(2026,6,1), date(2026,6,30))` and verify exactly one row per (design, grade) with the expected SUMs; rows outside the date window are excluded.
- **Automated**: TC-123 (basic aggregation), TC-124 (zero rows in window), TC-125 (window-edge inclusivity), TC-126 (multiple source types) all pass.
- **DoD**: Single class, single method, single SQL statement; outward_sum reads positive; coalesce guards on all three sums.

## Checkout
> *"LedgerAggregatesRepository.sum_deltas_by_source_type implemented as a single CASE-aggregated GROUP BY over tbl_stock_ledger. outward_sum inverted to read positive. Ready for DashboardService in T-061."*
