from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base, TimestampMixin
from src.infrastructure.db.models.master import GradeModel, TradingDesignModel
from src.infrastructure.db.models.transactions import SalesHeaderModel


class PriceMasterModel(Base, TimestampMixin):
    __tablename__ = "tbl_price_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    design_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_trading_design_master.design_id"), nullable=False
    )
    grade_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_grade_master.grade_id"), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    design: Mapped[TradingDesignModel] = relationship(lazy="joined")
    grade: Mapped[GradeModel] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "design_id", "grade_id", "effective_from",
            name="uq_price_design_grade_effective",
        ),
        CheckConstraint("unit_price >= 0", name="ck_price_master_unit_price_nonneg"),
    )


class InvoiceHeaderModel(Base, TimestampMixin):
    __tablename__ = "tbl_invoice_header"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    sales_header_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_sales_header.header_id"), unique=True, nullable=False
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # DS-023: status CHECK constraint ('PENDING'|'PARTIAL'|'PAID') added manually in
    # migration T-074 — autogenerate misses inline CHECK constraints (DS-009).
    status: Mapped[str] = mapped_column(String(10), default="PENDING", nullable=False)

    lines: Mapped[list["InvoiceLineModel"]] = relationship(back_populates="invoice_header")
    payments: Mapped[list["PaymentModel"]] = relationship(back_populates="invoice_header")
    sales_header: Mapped[SalesHeaderModel] = relationship(lazy="joined")


class InvoiceLineModel(Base, TimestampMixin):
    __tablename__ = "tbl_invoice_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_header_id: Mapped[int] = mapped_column(
        ForeignKey("tbl_invoice_header.id"), nullable=False
    )
    sales_line_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tbl_sales_line.line_id"), unique=True, nullable=False
    )
    # DS-022: design_id + grade_id are denormalized plain integers — NOT FKs to master
    # tables. unit_price snapshotted at invoice creation — NOT a FK to tbl_price_master.
    design_id: Mapped[int] = mapped_column(Integer, nullable=False)
    grade_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    invoice_header: Mapped["InvoiceHeaderModel"] = relationship(back_populates="lines")


class PaymentModel(Base, TimestampMixin):
    __tablename__ = "tbl_payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_header_id: Mapped[int] = mapped_column(
        ForeignKey("tbl_invoice_header.id"), nullable=False
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice_header: Mapped["InvoiceHeaderModel"] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )
