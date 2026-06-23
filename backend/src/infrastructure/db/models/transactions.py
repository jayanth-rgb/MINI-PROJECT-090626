from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base, TimestampMixin


# ──────────────────────────────────────────────────────────────────────────────
# Inward (F-007)
# ──────────────────────────────────────────────────────────────────────────────


class InwardHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_inward_header"

    header_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_supplier_master.supplier_id", ondelete="RESTRICT"),
        nullable=False,
    )
    # DS-013: denormalized snapshot of supplier.place at save time.
    place: Mapped[str] = mapped_column(Text, nullable=False)
    entered_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_staff_master.staff_id", ondelete="RESTRICT"),
        nullable=False,
    )

    lines: Mapped[list["InwardLineModel"]] = relationship(
        "InwardLineModel",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        Index("ix_inward_header_purchase_date", "purchase_date"),
    )


class InwardLineModel(Base):
    __tablename__ = "tbl_inward_line"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    header_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_inward_header.header_id", ondelete="CASCADE"),
        nullable=False,
    )
    design_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_trading_design_master.design_id", ondelete="RESTRICT"),
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_grade_master.grade_id", ondelete="RESTRICT"),
        nullable=False,
    )
    nos: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("nos > 0", name="ck_inward_line_nos_positive"),
        Index("ix_inward_line_header", "header_id"),
        Index("ix_inward_line_dgd", "design_id", "grade_id", "header_id"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Sales (F-008)
# ──────────────────────────────────────────────────────────────────────────────


class SalesHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_sales_header"

    header_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sales_date: Mapped[date] = mapped_column(Date, nullable=False)
    dealer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_dealer_master.dealer_id", ondelete="RESTRICT"),
        nullable=False,
    )
    # DS-013: denormalized snapshot of dealer.place at save time.
    place: Mapped[str] = mapped_column(Text, nullable=False)
    loading_staff_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_staff_master.staff_id", ondelete="RESTRICT"),
        nullable=False,
    )
    verified_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_staff_master.staff_id", ondelete="RESTRICT"),
        nullable=False,
    )

    lines: Mapped[list["SalesLineModel"]] = relationship(
        "SalesLineModel",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        Index("ix_sales_header_sales_date", "sales_date"),
        Index("ix_sales_header_dealer", "dealer_id"),
    )


class SalesLineModel(Base):
    __tablename__ = "tbl_sales_line"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    header_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_sales_header.header_id", ondelete="CASCADE"),
        nullable=False,
    )
    design_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_trading_design_master.design_id", ondelete="RESTRICT"),
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_grade_master.grade_id", ondelete="RESTRICT"),
        nullable=False,
    )
    nos: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("nos > 0", name="ck_sales_line_nos_positive"),
        Index("ix_sales_line_header", "header_id"),
        Index("ix_sales_line_dgd", "design_id", "grade_id", "header_id"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Adjustment (F-009)
# ──────────────────────────────────────────────────────────────────────────────


class AdjustmentHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_adjustment_header"

    header_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_date: Mapped[date] = mapped_column(Date, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    # AC-034: design_id on header (single-design per adjustment, not per line).
    design_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_trading_design_master.design_id", ondelete="RESTRICT"),
        nullable=False,
    )
    entered_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_staff_master.staff_id", ondelete="RESTRICT"),
        nullable=False,
    )

    lines: Mapped[list["AdjustmentLineModel"]] = relationship(
        "AdjustmentLineModel",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "stock_date <= entry_date",
            name="ck_adjustment_header_dates",
        ),
        Index(
            "ix_adjustment_header_design_stock_date",
            "design_id",
            "stock_date",
        ),
    )


class AdjustmentLineModel(Base):
    __tablename__ = "tbl_adjustment_line"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    header_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_adjustment_header.header_id", ondelete="CASCADE"),
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_grade_master.grade_id", ondelete="RESTRICT"),
        nullable=False,
    )
    software_cb: Mapped[int] = mapped_column(Integer, nullable=False)
    physical_cb: Mapped[int] = mapped_column(Integer, nullable=False)
    # Persisted (not GENERATED) so it survives ledger recomputes per DS-003 / AC-038.
    difference: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "physical_cb >= 0",
            name="ck_adjustment_line_physical_cb_nonneg",
        ),
        Index("ix_adjustment_line_header", "header_id"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Stock Ledger (M-003 materialized projection per DS-003)
# ──────────────────────────────────────────────────────────────────────────────


class StockLedgerModel(Base, TimestampMixin):
    __tablename__ = "tbl_stock_ledger"

    ledger_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    design_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_trading_design_master.design_id", ondelete="RESTRICT"),
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tbl_grade_master.grade_id", ondelete="RESTRICT"),
        nullable=False,
    )
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_header_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_line_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    # DS-003: materialized running balance; back-dated inserts trigger
    # domain.stock._recompute_forward to rewrite later rows in this (design, grade) series.
    running_balance: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('inward', 'sale', 'adjustment')",
            name="ck_stock_ledger_source_type",
        ),
        # Composite index: DS-002 SELECT FOR UPDATE on latest row,
        # DS-004 closing_balance as-of-date lookup,
        # DS-003 _recompute_forward range scan.
        Index(
            "ix_stock_ledger_dgt",
            "design_id",
            "grade_id",
            text("txn_date DESC"),
            text("ledger_id DESC"),
        ),
    )
