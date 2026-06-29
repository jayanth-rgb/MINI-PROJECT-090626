# T-062 — `application/services/sales_report_service.py` — F-011 dual payload

**Module:** M-005 · **Depends on:** T-058 · **DS:** DS-013, DS-017

## Context anchor
Group B (parallel-eligible with T-061 — both depend on Group A only). Reads from existing S2 `models/transactions.py` (`SalesHeaderModel`, `SalesLineModel`) + S1 `models/master.py` (`TradingDesignModel`, `GradeModel`, `DealerModel`). Projects into the schemas T-058 created.

**DS-017** is load-bearing: the same `_build_filters(...)` helper is applied to BOTH the consolidation and the transactions query. Hand-maintaining matching WHERE clauses across two SELECTs would risk silent AC-050 violations.

`TransactionRow.place` is read from the **`tbl_sales_header.place_snapshot`** column captured at sale time per **DS-013** — NOT from `dealer.place` live. (If dealer's place changes after the sale, the report still shows the historical value.)

## Implementation logic

```python
# backend/src/application/services/sales_report_service.py
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from src.infrastructure.db.models.master import DealerModel, GradeModel, TradingDesignModel
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from src.presentation.schemas.sales_report import (
    ConsolidationRow,
    SalesReportResponse,
    TransactionRow,
)


class SalesReportService:
    """M-005: dual-payload sales report (Consolidation + Transactions) with shared filters (DS-017)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def generate(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        dealer_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> SalesReportResponse:
        filters = self._build_filters(date_from, date_to, dealer_ids, places, design_ids)

        consolidation = self._query_consolidation(filters)
        transactions = self._query_transactions(filters)

        # AC-050: defense-in-depth — shared filter builder guarantees parity by construction,
        # but assert at runtime so any future refactor can't silently break reconciliation.
        consol_total = sum(r.total_nos for r in consolidation)
        txn_total = sum(r.nos for r in transactions)
        assert consol_total == txn_total, (
            f"AC-050 reconciliation broken: consolidation sum={consol_total} "
            f"!= transactions sum={txn_total}"
        )

        return SalesReportResponse(consolidation=consolidation, transactions=transactions)

    # ---- internals ----

    def _build_filters(
        self,
        date_from: date | None,
        date_to: date | None,
        dealer_ids: list[int] | None,
        places: list[str] | None,
        design_ids: list[int] | None,
    ) -> list[ColumnElement[bool]]:
        """Build the WHERE predicates shared by both queries (DS-017). All filters optional and
        multi-select per RULE-018. An empty list (no filters) returns the full dataset."""
        conds: list[ColumnElement[bool]] = []
        if date_from is not None:
            conds.append(SalesHeaderModel.sales_date >= date_from)
        if date_to is not None:
            conds.append(SalesHeaderModel.sales_date <= date_to)
        if dealer_ids:
            conds.append(SalesHeaderModel.dealer_id.in_(dealer_ids))
        if places:
            conds.append(SalesHeaderModel.place_snapshot.in_(places))  # DS-013 denormalized snapshot
        if design_ids:
            conds.append(SalesLineModel.design_id.in_(design_ids))
        return conds

    def _query_consolidation(self, filters: list[ColumnElement[bool]]) -> list[ConsolidationRow]:
        stmt = (
            select(
                SalesLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                SalesLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                func.sum(SalesLineModel.nos).label("total_nos"),
            )
            .join(SalesHeaderModel, SalesHeaderModel.header_id == SalesLineModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == SalesLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == SalesLineModel.grade_id)
            .where(*filters)
            .group_by(
                SalesLineModel.design_id,
                TradingDesignModel.design_name,
                TradingDesignModel.size,
                SalesLineModel.grade_id,
                GradeModel.grade_code,
            )
            .order_by(TradingDesignModel.design_name.asc(), GradeModel.grade_code.asc())  # RULE-019
        )
        return [ConsolidationRow.model_validate(row, from_attributes=True) for row in self.session.execute(stmt).all()]

    def _query_transactions(self, filters: list[ColumnElement[bool]]) -> list[TransactionRow]:
        stmt = (
            select(
                SalesHeaderModel.sales_date.label("sales_date"),
                SalesHeaderModel.dealer_id.label("dealer_id"),
                DealerModel.dealer_name.label("dealer_name"),
                SalesHeaderModel.place_snapshot.label("place"),  # DS-013
                SalesLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                SalesLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                SalesLineModel.nos.label("nos"),
            )
            .join(SalesLineModel, SalesLineModel.header_id == SalesHeaderModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == SalesLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == SalesLineModel.grade_id)
            .join(DealerModel, DealerModel.dealer_id == SalesHeaderModel.dealer_id)
            .where(*filters)
            .order_by(SalesHeaderModel.sales_date.asc(), SalesHeaderModel.header_id.asc())  # RULE-020
        )
        return [TransactionRow.model_validate(row, from_attributes=True) for row in self.session.execute(stmt).all()]
```

## Constraints
- **One** filter-predicate builder; applied to BOTH queries (DS-017). No inline WHEREs in either query method.
- `TransactionRow.place` reads from `SalesHeaderModel.place_snapshot` (DS-013), NOT `DealerModel.place`. Verify the S2 column name in `models/transactions.py` matches `place_snapshot`; if it's `place` instead, use that — but it must be the column on the sales_header, not joined live from dealer.
- AC-050 reconciliation assertion is mandatory — defense-in-depth even though DS-017's shared predicate makes violation structurally impossible.
- Sort happens in SQL (RULE-019 + RULE-020) — `order_by` clauses are not optional.
- No `LIMIT`/`OFFSET` — sprint is read-everything-in-window; pagination is V2 (not in scope).
- Returns `SalesReportResponse` (not raw lists) — single response object per AC-049.

## Do not touch
- `backend/src/infrastructure/db/repositories/transactions.py` (S2)
- Any model file
- `backend/src/presentation/schemas/sales_report.py` (T-058 owns)
- Any other service
- Any test file

## ⚠ Pre-implementation read
Before writing this file, **read** `backend/src/infrastructure/db/models/transactions.py` and confirm:
1. The `SalesHeaderModel` column name for the denormalized place — `place_snapshot` or `place`. Use whatever exists.
2. The `SalesLineModel.nos` column name (LLD references `nos`; should match).
3. The primary-key column name on `SalesHeaderModel` — `header_id` or `sales_header_id`. Use whatever exists.

If any of these differ from the pseudocode above, mirror the actual model — the LLD's column names are nominal.

## Success criteria
- **Manual**: with seed data, `generate(date(2026,6,1), date(2026,6,30))` returns a SalesReportResponse where `sum(transactions.nos) == sum(consolidation.total_nos)` and rows are sorted per RULE-019/020.
- **Automated**: all 14 TCs pass.
- **DoD**: `_build_filters` is the single source of WHERE clauses; both query methods use `*filters`; AC-050 assertion present; sorts inside SQL.

## Checkout
> *"SalesReportService.generate implemented — shared _build_filters predicate (DS-017) drives both queries; AC-050 assertion runs after, RULE-019/020 sorts in SQL. Ready for router wiring in T-065."*
