"""transactions and stock ledger; uplift S1 created_at to TIMESTAMPTZ

Revision ID: 0003_transaction_and_ledger_tables
Revises: 0002_master_tables
Create Date: 2026-06-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_tx_ledger"
down_revision = "0002_master_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Step 1: ALTER S1 created_at columns to TIMESTAMPTZ (DS-014, closes TD-007) ===
    for table in (
        "tbl_supplier_master",
        "tbl_staff_master",
        "tbl_dealer_master",
        "tbl_trading_design_master",
    ):
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=sa.text("now()"),
            postgresql_using="created_at AT TIME ZONE 'UTC'",
        )

    # === Step 2: CREATE 3 header tables (parents) ===
    op.create_table(
        "tbl_inward_header",
        sa.Column("header_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=False),
        sa.Column("place", sa.Text(), nullable=False),  # DS-013
        sa.Column("entered_by_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["tbl_supplier_master.supplier_id"],
            name="fk_inward_header_supplier_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entered_by_id"],
            ["tbl_staff_master.staff_id"],
            name="fk_inward_header_entered_by_id",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_inward_header_purchase_date",
        "tbl_inward_header",
        ["purchase_date"],
    )

    op.create_table(
        "tbl_sales_header",
        sa.Column("header_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sales_date", sa.Date(), nullable=False),
        sa.Column("dealer_id", sa.BigInteger(), nullable=False),
        sa.Column("place", sa.Text(), nullable=False),  # DS-013
        sa.Column("loading_staff_id", sa.BigInteger(), nullable=False),
        sa.Column("verified_by_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["dealer_id"],
            ["tbl_dealer_master.dealer_id"],
            name="fk_sales_header_dealer_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["loading_staff_id"],
            ["tbl_staff_master.staff_id"],
            name="fk_sales_header_loading_staff_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_id"],
            ["tbl_staff_master.staff_id"],
            name="fk_sales_header_verified_by_id",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_sales_header_sales_date",
        "tbl_sales_header",
        ["sales_date"],
    )
    op.create_index(
        "ix_sales_header_dealer",
        "tbl_sales_header",
        ["dealer_id"],
    )

    op.create_table(
        "tbl_adjustment_header",
        sa.Column("header_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("stock_date", sa.Date(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("design_id", sa.BigInteger(), nullable=False),  # AC-034 single-design on header
        sa.Column("entered_by_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["design_id"],
            ["tbl_trading_design_master.design_id"],
            name="fk_adjustment_header_design_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entered_by_id"],
            ["tbl_staff_master.staff_id"],
            name="fk_adjustment_header_entered_by_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "stock_date <= entry_date",
            name="ck_adjustment_header_dates",
        ),
    )
    op.create_index(
        "ix_adjustment_header_design_stock_date",
        "tbl_adjustment_header",
        ["design_id", "stock_date"],
    )

    # === Step 3: CREATE 3 line tables (FK children of headers, CASCADE on header delete) ===
    op.create_table(
        "tbl_inward_line",
        sa.Column("line_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("header_id", sa.BigInteger(), nullable=False),
        sa.Column("design_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column("nos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["header_id"],
            ["tbl_inward_header.header_id"],
            name="fk_inward_line_header_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["design_id"],
            ["tbl_trading_design_master.design_id"],
            name="fk_inward_line_design_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["tbl_grade_master.grade_id"],
            name="fk_inward_line_grade_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("nos > 0", name="ck_inward_line_nos_positive"),
    )
    op.create_index("ix_inward_line_header", "tbl_inward_line", ["header_id"])
    op.create_index(
        "ix_inward_line_dgd",
        "tbl_inward_line",
        ["design_id", "grade_id", "header_id"],
    )

    op.create_table(
        "tbl_sales_line",
        sa.Column("line_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("header_id", sa.BigInteger(), nullable=False),
        sa.Column("design_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column("nos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["header_id"],
            ["tbl_sales_header.header_id"],
            name="fk_sales_line_header_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["design_id"],
            ["tbl_trading_design_master.design_id"],
            name="fk_sales_line_design_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["tbl_grade_master.grade_id"],
            name="fk_sales_line_grade_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("nos > 0", name="ck_sales_line_nos_positive"),
    )
    op.create_index("ix_sales_line_header", "tbl_sales_line", ["header_id"])
    op.create_index(
        "ix_sales_line_dgd",
        "tbl_sales_line",
        ["design_id", "grade_id", "header_id"],
    )

    op.create_table(
        "tbl_adjustment_line",
        sa.Column("line_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("header_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column("software_cb", sa.Integer(), nullable=False),
        sa.Column("physical_cb", sa.Integer(), nullable=False),
        sa.Column("difference", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["header_id"],
            ["tbl_adjustment_header.header_id"],
            name="fk_adjustment_line_header_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["tbl_grade_master.grade_id"],
            name="fk_adjustment_line_grade_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "physical_cb >= 0",
            name="ck_adjustment_line_physical_cb_nonneg",
        ),
    )
    op.create_index(
        "ix_adjustment_line_header",
        "tbl_adjustment_line",
        ["header_id"],
    )

    # === Step 4: CREATE tbl_stock_ledger + composite DESC index (DS-002 / DS-003) ===
    op.create_table(
        "tbl_stock_ledger",
        sa.Column("ledger_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("design_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_header_id", sa.BigInteger(), nullable=True),
        sa.Column("source_line_id", sa.BigInteger(), nullable=True),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("running_balance", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["design_id"],
            ["tbl_trading_design_master.design_id"],
            name="fk_stock_ledger_design_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["tbl_grade_master.grade_id"],
            name="fk_stock_ledger_grade_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "source_type IN ('inward', 'sale', 'adjustment')",
            name="ck_stock_ledger_source_type",
        ),
    )
    # Composite index with DESC on txn_date + ledger_id — op.create_index does not
    # express per-column DESC natively; use raw DDL.
    op.execute(
        "CREATE INDEX ix_stock_ledger_dgt ON tbl_stock_ledger "
        "(design_id, grade_id, txn_date DESC, ledger_id DESC)"
    )


def downgrade() -> None:
    # Drop in reverse FK dependency order.
    op.execute("DROP INDEX IF EXISTS ix_stock_ledger_dgt")
    op.drop_table("tbl_stock_ledger")

    op.drop_index("ix_adjustment_line_header", table_name="tbl_adjustment_line")
    op.drop_table("tbl_adjustment_line")

    op.drop_index("ix_sales_line_dgd", table_name="tbl_sales_line")
    op.drop_index("ix_sales_line_header", table_name="tbl_sales_line")
    op.drop_table("tbl_sales_line")

    op.drop_index("ix_inward_line_dgd", table_name="tbl_inward_line")
    op.drop_index("ix_inward_line_header", table_name="tbl_inward_line")
    op.drop_table("tbl_inward_line")

    op.drop_index(
        "ix_adjustment_header_design_stock_date",
        table_name="tbl_adjustment_header",
    )
    op.drop_table("tbl_adjustment_header")

    op.drop_index("ix_sales_header_dealer", table_name="tbl_sales_header")
    op.drop_index("ix_sales_header_sales_date", table_name="tbl_sales_header")
    op.drop_table("tbl_sales_header")

    op.drop_index("ix_inward_header_purchase_date", table_name="tbl_inward_header")
    op.drop_table("tbl_inward_header")

    # Revert TIMESTAMPTZ on 4 S1 columns.
    for table in (
        "tbl_supplier_master",
        "tbl_staff_master",
        "tbl_dealer_master",
        "tbl_trading_design_master",
    ):
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("now()"),
        )
