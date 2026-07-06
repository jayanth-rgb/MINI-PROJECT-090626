# T-077 — `services/inward_report_service.py` — InwardReportService

**Module:** M-009 · **Wave:** 2 (after T-076) · **Depends on:** T-076 (schemas/inward_report.py)

## Context anchor

Mirrors `SalesReportService` (S3 T-062) exactly, but for inward data (tbl_inward_header + tbl_inward_line). DS-017: shared filter predicate guarantees the reconciliation invariant `sum(transactions.nos) == sum(consolidation.total_nos)` by construction. DS-013: `place` read from `tbl_inward_header.place` as-is (no re-join to supplier master).

## Implementation logic

```python
# backend/src/application/services/inward_report_service.py
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from infrastructure.db.models.transactions import InwardHeaderModel, InwardLineModel
from infrastructure.db.models.master import TradingDesignModel, GradeModel, SupplierModel
from presentation.schemas.inward_report import (
    InwardConsolidationRow, InwardTransactionRow, InwardReportResponse
)


class InwardReportService:

    def __init__(self, db: Session) -> None:
        self._db = db

    def generate(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        supplier_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> InwardReportResponse:
        # Step 1: Build shared predicate list
        predicates = []
        if date_from:
            predicates.append(InwardHeaderModel.purchase_date >= date_from)
        if date_to:
            predicates.append(InwardHeaderModel.purchase_date <= date_to)
        if supplier_ids:
            predicates.append(InwardHeaderModel.supplier_id.in_(supplier_ids))
        if places:
            predicates.append(InwardHeaderModel.place.in_(places))
        if design_ids:
            predicates.append(InwardLineModel.design_id.in_(design_ids))

        # Step 2: Consolidation query
        consolidation_stmt = (
            select(
                InwardLineModel.design_id,
                TradingDesignModel.design_name,
                TradingDesignModel.size,
                InwardLineModel.grade_id,
                GradeModel.grade_code,
                func.sum(InwardLineModel.nos).label("total_nos"),
            )
            .join(InwardHeaderModel, InwardLineModel.inward_header_id == InwardHeaderModel.id)
            .join(TradingDesignModel, InwardLineModel.design_id == TradingDesignModel.id)
            .join(GradeModel, InwardLineModel.grade_id == GradeModel.id)
            .where(*predicates)
            .group_by(
                InwardLineModel.design_id, InwardLineModel.grade_id,
                TradingDesignModel.design_name, TradingDesignModel.size, GradeModel.grade_code
            )
            .order_by(TradingDesignModel.design_name.asc(), GradeModel.grade_code.asc())
        )
        consolidation_rows = self._db.execute(consolidation_stmt).all()

        # Step 3: Transactions query (same predicates)
        transactions_stmt = (
            select(
                InwardHeaderModel.purchase_date,
                InwardHeaderModel.supplier_id,
                SupplierModel.supplier_name,
                InwardHeaderModel.place,   # DS-013: snapshot
                InwardLineModel.design_id,
                TradingDesignModel.design_name,
                TradingDesignModel.size,
                InwardLineModel.grade_id,
                GradeModel.grade_code,
                InwardLineModel.nos,
            )
            .join(InwardHeaderModel, InwardLineModel.inward_header_id == InwardHeaderModel.id)
            .join(TradingDesignModel, InwardLineModel.design_id == TradingDesignModel.id)
            .join(GradeModel, InwardLineModel.grade_id == GradeModel.id)
            .join(SupplierModel, InwardHeaderModel.supplier_id == SupplierModel.id)
            .where(*predicates)
            .order_by(InwardHeaderModel.purchase_date.asc(), InwardHeaderModel.id.asc())
        )
        transaction_rows = self._db.execute(transactions_stmt).all()

        # Step 4: Reconciliation assert (defense-in-depth per DS-017)
        txn_total = sum(r.nos for r in transaction_rows)
        con_total = sum(r.total_nos for r in consolidation_rows)
        assert txn_total == con_total, (
            f"Inward report reconciliation failed: transactions.nos={txn_total} != "
            f"consolidation.total_nos={con_total}"
        )

        return InwardReportResponse(
            consolidation=[InwardConsolidationRow.model_validate(r, from_attributes=True) for r in consolidation_rows],
            transactions=[InwardTransactionRow.model_validate(r, from_attributes=True) for r in transaction_rows],
        )
```

## Constraints

- The SAME `predicates` list must be used for BOTH queries (DS-017 shared predicate guarantee).
- `place` comes from `InwardHeaderModel.place` (DS-013 snapshot) — not from `SupplierModel`.
- `AssertionError` from the reconciliation check is an internal invariant violation (never expected to fire in production). Caller does not need to catch it.
- No pagination — returns full dataset matching filters (mirrors SalesReportService behavior).

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: Invoke `InwardReportService(db).generate()` with seeded inward data; `response.consolidation` and `response.transactions` are non-empty; sums match.
- **Automated**: TC-195 (reconciliation, 3 lines), TC-196 (date filter reduces to 1 line), TC-197 (ordering).
- **DoD**: `InwardReportService` exported. `generate()` with 5 optional params. Shared predicate. Reconciliation assert. Correct ordering on both sections.

## Checkout

> *"InwardReportService created. generate() with shared predicate, reconciliation assert, dual-query pattern mirrors SalesReportService. TC-195..TC-197 covered. Ready for T-078 (router) and T-087 (export)."*
