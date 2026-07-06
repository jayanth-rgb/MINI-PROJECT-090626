# T-079 — `infrastructure/db/models/pricing.py` — ORM for 4 V2 pricing tables

**Module:** M-011 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Creates 4 ORM models for M-011 (Pricing & Invoicing). Builds on S1 master models (TradingDesignModel, GradeModel) and S2 transaction models (SalesHeaderModel, SalesLineModel) — read-only FK references. DS-022: `unit_price` snapshotted on `InvoiceLineModel` at creation — FK to price_master deliberately NOT used. DS-023: UNIQUE(sales_header_id) on InvoiceHeaderModel enforces one-invoice-per-sale.

## Implementation logic

```python
# backend/src/infrastructure/db/models/pricing.py
from decimal import Decimal
from sqlalchemy import (Boolean, Date, ForeignKey, Integer, Numeric, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.db.base import Base, TimestampMixin
from infrastructure.db.models.master import TradingDesignModel, GradeModel
from infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel


class PriceMasterModel(Base, TimestampMixin):
    __tablename__ = "tbl_price_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("tbl_trading_design_master.id"), nullable=False)
    grade_id: Mapped[int] = mapped_column(ForeignKey("tbl_grade_master.id"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    design: Mapped[TradingDesignModel] = relationship(lazy="joined")
    grade: Mapped[GradeModel] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint("design_id", "grade_id", "effective_from",
                         name="uq_price_design_grade_effective"),
    )


class InvoiceHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_invoice_header"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    sales_header_id: Mapped[int] = mapped_column(
        ForeignKey("tbl_sales_header.id"), unique=True, nullable=False
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="PENDING", nullable=False)

    lines: Mapped[list["InvoiceLineModel"]] = relationship(back_populates="invoice_header")
    payments: Mapped[list["PaymentModel"]] = relationship(back_populates="invoice_header")
    sales_header: Mapped[SalesHeaderModel] = relationship(lazy="joined")


class InvoiceLineModel(Base, TimestampMixin):
    __tablename__ = "tbl_invoice_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_header_id: Mapped[int] = mapped_column(ForeignKey("tbl_invoice_header.id"), nullable=False)
    sales_line_id: Mapped[int] = mapped_column(
        ForeignKey("tbl_sales_line.id"), unique=True, nullable=False
    )
    design_id: Mapped[int] = mapped_column(Integer, nullable=False)
    grade_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    invoice_header: Mapped[InvoiceHeaderModel] = relationship(back_populates="lines")


class PaymentModel(Base, TimestampMixin):
    __tablename__ = "tbl_payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_header_id: Mapped[int] = mapped_column(ForeignKey("tbl_invoice_header.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice_header: Mapped[InvoiceHeaderModel] = relationship(back_populates="payments")
```

## Constraints

- `InvoiceLineModel.unit_price` is a plain `Numeric` column — NOT a FK to `tbl_price_master` (DS-022 snapshot invariant).
- `InvoiceLineModel.design_id` and `grade_id` are plain `Integer` columns — denormalized copy, not FKs.
- `PriceMasterModel.design` and `.grade` use `lazy='joined'` so price listing returns design_name/grade_code without extra queries.
- Do NOT add `CHECK(status IN ('PENDING','PARTIAL','PAID'))` in ORM — add it manually in migration T-074 since SQLAlchemy autogenerate misses inline CHECK constraints.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `python -c "from src.infrastructure.db.models.pricing import PriceMasterModel, InvoiceHeaderModel, InvoiceLineModel, PaymentModel; print([m.__tablename__ for m in [PriceMasterModel, InvoiceHeaderModel, InvoiceLineModel, PaymentModel]])"` → 4 table names.
- **Automated**: T-080 (TC-187..TC-189) inserts and queries these models.
- **DoD**: 4 models exported. PriceMasterModel UniqueConstraint on 3 columns. InvoiceHeaderModel UNIQUE(sales_header_id). InvoiceLineModel UNIQUE(sales_line_id). No FK on InvoiceLineModel.unit_price.

## Checkout

> *"models/pricing.py created. 4 ORM models: PriceMasterModel, InvoiceHeaderModel, InvoiceLineModel, PaymentModel. Ready for T-080 (pricing repos) and T-074 (migration)."*
