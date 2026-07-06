"""V2 auth and pricing tables: tbl_user_master, tbl_price_master, tbl_invoice_header, tbl_invoice_line, tbl_payment

Revision ID: 0004_v2_auth_pricing_tables
Revises: 0003_tx_ledger
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_v2_auth_pricing_tables"
down_revision = "0003_tx_ledger"
branch_labels = None
depends_on = None

# PostgreSQL ENUM type for tbl_user_master.role (DS-009, DS-019)
# VARCHAR CHECK approach rejected: ORM uses sa.Enum with named type — migration follows ORM per DS-009.
user_role_enum = sa.Enum("STAFF", "VERIFIER", "SUPERVISOR", name="user_role_enum")


def upgrade() -> None:
    # tbl_user_master — M-008 Authentication & Authorization
    op.create_table(
        "tbl_user_master",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_user_master_username", "tbl_user_master", ["username"])

    # tbl_price_master — M-011 Pricing
    op.create_table(
        "tbl_price_master",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "design_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_trading_design_master.design_id"),
            nullable=False,
        ),
        sa.Column(
            "grade_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_grade_master.grade_id"),
            nullable=False,
        ),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "design_id", "grade_id", "effective_from",
            name="uq_price_design_grade_effective",
        ),
        sa.CheckConstraint("unit_price >= 0", name="ck_price_master_unit_price_nonneg"),
    )

    # tbl_invoice_header — M-011 Invoicing
    op.create_table(
        "tbl_invoice_header",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_number", sa.String(30), unique=True, nullable=False),
        sa.Column(
            "sales_header_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_sales_header.header_id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        # DS-023: CHECK added manually — autogenerate misses inline CHECK on VARCHAR columns (DS-009)
        sa.Column(
            "status",
            sa.String(10),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','PARTIAL','PAID')", name="ck_invoice_status"
        ),
    )
    op.create_index(
        "ix_invoice_header_invoice_date", "tbl_invoice_header", ["invoice_date"]
    )

    # tbl_invoice_line — M-011 Invoice Lines
    op.create_table(
        "tbl_invoice_line",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "invoice_header_id",
            sa.Integer(),
            sa.ForeignKey("tbl_invoice_header.id"),
            nullable=False,
        ),
        # DS-022: sales_line_id UNIQUE — one invoice line per sales line across the system
        sa.Column(
            "sales_line_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_sales_line.line_id"),
            unique=True,
            nullable=False,
        ),
        # DS-022: design_id + grade_id are denormalized snapshots — plain integers, no FK
        sa.Column("design_id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_invoice_line_header", "tbl_invoice_line", ["invoice_header_id"]
    )

    # tbl_payment — M-011 Payments (append-only)
    op.create_table(
        "tbl_payment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "invoice_header_id",
            sa.Integer(),
            sa.ForeignKey("tbl_invoice_header.id"),
            nullable=False,
        ),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )
    op.create_index(
        "ix_payment_invoice_header", "tbl_payment", ["invoice_header_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_payment_invoice_header", table_name="tbl_payment")
    op.drop_table("tbl_payment")
    op.drop_index("ix_invoice_line_header", table_name="tbl_invoice_line")
    op.drop_table("tbl_invoice_line")
    op.drop_index("ix_invoice_header_invoice_date", table_name="tbl_invoice_header")
    op.drop_table("tbl_invoice_header")
    op.drop_table("tbl_price_master")
    op.drop_index("ix_user_master_username", table_name="tbl_user_master")
    op.drop_table("tbl_user_master")
    user_role_enum.drop(op.get_bind())
