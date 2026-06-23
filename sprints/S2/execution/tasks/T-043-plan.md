# T-043 — Transaction + StockLedger repositories

**Module:** M-007 · **Depends on:** T-042 · **DS:** DS-002, DS-003, DS-012

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/transactions.py
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.models.transactions import (
    InwardHeaderModel, InwardLineModel,
    SalesHeaderModel, SalesLineModel,
    AdjustmentHeaderModel, AdjustmentLineModel,
    StockLedgerModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class InwardHeaderRepository(BaseRepository[InwardHeaderModel]):
    def create_with_lines(self, header_payload: dict, line_payloads: list[dict]) -> InwardHeaderModel:
        header = InwardHeaderModel(**header_payload)
        self.session.add(header)
        self.session.flush()  # ensures header.header_id is assigned
        for lp in line_payloads:
            self.session.add(InwardLineModel(header_id=header.header_id, **lp))
        self.session.flush()
        return header


class SalesHeaderRepository(BaseRepository[SalesHeaderModel]):
    def create_with_lines(self, header_payload: dict, line_payloads: list[dict]) -> SalesHeaderModel:
        header = SalesHeaderModel(**header_payload)
        self.session.add(header)
        self.session.flush()
        for lp in line_payloads:
            self.session.add(SalesLineModel(header_id=header.header_id, **lp))
        self.session.flush()
        return header


class AdjustmentHeaderRepository(BaseRepository[AdjustmentHeaderModel]):
    def create_with_lines(self, header_payload: dict, line_payloads: list[dict]) -> AdjustmentHeaderModel:
        # Same pattern.
        ...


class StockLedgerRepository(BaseRepository[StockLedgerModel]):
    def latest_for_design_grade(
        self, design_id: int, grade_id: int, for_update: bool = False
    ) -> StockLedgerModel | None:
        stmt = (
            select(StockLedgerModel)
            .where(StockLedgerModel.design_id == design_id, StockLedgerModel.grade_id == grade_id)
            .order_by(StockLedgerModel.txn_date.desc(), StockLedgerModel.ledger_id.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.execute(stmt).scalar_one_or_none()

    def latest_as_of(self, design_id: int, grade_id: int, as_of_date: date) -> StockLedgerModel | None:
        stmt = (
            select(StockLedgerModel)
            .where(
                StockLedgerModel.design_id == design_id,
                StockLedgerModel.grade_id == grade_id,
                StockLedgerModel.txn_date <= as_of_date,
            )
            .order_by(StockLedgerModel.txn_date.desc(), StockLedgerModel.ledger_id.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def rows_after(self, design_id: int, grade_id: int, after_date_inclusive: date) -> list[StockLedgerModel]:
        stmt = (
            select(StockLedgerModel)
            .where(
                StockLedgerModel.design_id == design_id,
                StockLedgerModel.grade_id == grade_id,
                StockLedgerModel.txn_date >= after_date_inclusive,
            )
            .order_by(StockLedgerModel.txn_date.asc(), StockLedgerModel.ledger_id.asc())
        )
        return list(self.session.execute(stmt).scalars())

    def insert(self, data: dict) -> StockLedgerModel:
        row = StockLedgerModel(**data)
        self.session.add(row)
        self.session.flush()
        return row
```

## Constraints
- DS-002: `latest_for_design_grade(for_update=True)` is the lock acquisition point. NO other write path may insert into `tbl_stock_ledger` without holding this lock first.
- DS-003: `latest_as_of(as_of_date)` is the O(1) lookup driving `closing_balance` AND `opening_balance` (via `as_of_date = month_first - 1 day`).
- DS-012: All 4 repos subclass `BaseRepository[TModel]`; no raw SQL.
- `latest_for_design_grade` ordering: `txn_date DESC, ledger_id DESC` — ledger_id breaks ties when multiple ledger rows share the same txn_date.

## Do not touch
Any other file.

## Success criteria
- **Manual:** All 4 repos importable; method signatures match LLD.
- **Automated:** Domain tests TC-079..TC-087 exercise these methods; TC-087 concurrency verifies `with_for_update()` produces lock contention.
- **DoD:** `create_with_lines` returns a flushed header with all line FKs populated; `StockLedgerRepository.insert` returns a flushed row with `ledger_id` assigned.

## Checkout prompt
*"4 transaction repos created. StockLedgerRepository ready for SELECT FOR UPDATE."*
