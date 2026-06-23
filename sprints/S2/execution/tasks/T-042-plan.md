# T-042 — Transaction + Stock Ledger ORM models

**Module:** M-007 · **Depends on:** T-041 · **DS:** DS-007, DS-008, DS-013, DS-014

## Implementation logic

```python
# backend/src/infrastructure/db/models/transactions.py
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base, TimestampMixin


class InwardHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_inward_header"
    header_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_supplier_master.supplier_id", ondelete="RESTRICT"),
        nullable=False,
    )
    place: Mapped[str] = mapped_column(Text, nullable=False)  # DS-013 snapshot
    entered_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_staff_master.staff_id", ondelete="RESTRICT"),
        nullable=False,
    )
    lines = relationship("InwardLineModel", cascade="all, delete-orphan", lazy="joined")
    __table_args__ = (
        Index("ix_inward_header_purchase_date", "purchase_date"),
    )


class InwardLineModel(Base):
    __tablename__ = "tbl_inward_line"
    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    header_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_inward_header.header_id", ondelete="CASCADE"), nullable=False
    )
    design_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_trading_design_master.design_id", ondelete="RESTRICT"), nullable=False
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_grade_master.grade_id", ondelete="RESTRICT"), nullable=False
    )
    nos: Mapped[int] = mapped_column(Integer, nullable=False)
    __table_args__ = (
        CheckConstraint("nos > 0", name="ck_inward_line_nos_positive"),
        Index("ix_inward_line_header", "header_id"),
        Index("ix_inward_line_dgd", "design_id", "grade_id", "header_id"),
    )


# SalesHeaderModel — mirror with dealer_id + place (DS-013) + loading_staff_id + verified_by_id.
# SalesLineModel — mirror of InwardLineModel with FK to sales_header.
# AdjustmentHeaderModel — design_id on header (AC-034); stock_date, entry_date; CHECK(stock_date <= entry_date).
# AdjustmentLineModel — grade_id, software_cb, physical_cb (CHECK >= 0), difference. No CHECK on difference (can be negative).
# StockLedgerModel — design_id + grade_id + txn_date + source_type (CHECK IN list) + source_header_id (nullable) + source_line_id (nullable) + delta + running_balance + created_at (via TimestampMixin).
#   __table_args__: (CheckConstraint("source_type IN ('inward','sale','adjustment')"),
#                    Index("ix_stock_ledger_dgt", "design_id", "grade_id", text("txn_date DESC"), text("ledger_id DESC")))
```

Full content of all 7 models follows the same pattern. Reference [sprints/S2/design/schema.json](../../design/schema.json) for exact column types/constraints.

## Constraints
- DS-007: ORM models in `models/transactions.py` only; no business logic here.
- DS-013: `place` is a `Text NOT NULL` column on `tbl_inward_header` AND `tbl_sales_header` (denormalized snapshot at save).
- DS-014: All headers carry `created_at` via `TimestampMixin` (now TIMESTAMPTZ from T-041).
- AC-034: AdjustmentHeader has `design_id` (single-design); AdjustmentLine does NOT.
- Adjustment line: `software_cb`, `physical_cb`, `difference` all `Integer NOT NULL`; `difference` is persisted (not GENERATED).
- Stock ledger composite index uses `txn_date DESC, ledger_id DESC` for the closing-balance-as-of-date lookup and SELECT FOR UPDATE.
- DB CHECK constraints with explicit names: `ck_*_nos_positive`, `ck_adjustment_header_dates`, `ck_adjustment_line_physical_cb_nonneg`, `ck_stock_ledger_source_type`.

## Do not touch
Any other file.

## Success criteria
- **Manual:** All 7 model classes importable; Base.metadata.tables contains 7 new entries.
- **Automated:** `Base.metadata.create_all(test_engine)` succeeds; downstream T-044 migration matches autogenerate output; TC-053/064/069/088/089 fire the CHECK violations they expect.
- **DoD:** 7 models, all CHECK constraints declared, composite stock_ledger index in place, relationships configured.

## Checkout prompt
*"7 ORM models created with CHECK constraints + composite stock_ledger index. TIMESTAMPTZ via T-041 mixin."*
