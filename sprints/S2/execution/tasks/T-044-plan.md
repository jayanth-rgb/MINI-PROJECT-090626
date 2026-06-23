# T-044 — Alembic migration 0003

**Module:** M-007 · **Depends on:** T-041, T-042 · **DS:** DS-009, DS-014

## Implementation logic

```python
"""transactions and stock ledger; uplift S1 created_at to TIMESTAMPTZ

Revision ID: 0003_transaction_and_ledger_tables
Revises: 0002_master_tables
Create Date: 2026-06-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_transaction_and_ledger_tables"
down_revision = "0002_master_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Step 1: ALTER S1 created_at columns to TIMESTAMPTZ (DS-014) ===
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
        sa.Column("place", sa.Text(), nullable=False),
        sa.Column("entered_by_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["supplier_id"], ["tbl_supplier_master.supplier_id"], name="fk_inward_header_supplier_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entered_by_id"], ["tbl_staff_master.staff_id"], name="fk_inward_header_entered_by_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_inward_header_purchase_date", "tbl_inward_header", ["purchase_date"])

    # tbl_sales_header — same shape with dealer_id, place, loading_staff_id, verified_by_id; indexes on sales_date and dealer_id.

    # tbl_adjustment_header — design_id on header (AC-034), stock_date, entry_date, entered_by_id.
    # + CheckConstraint("stock_date <= entry_date", name="ck_adjustment_header_dates")
    # + Index("ix_adjustment_header_design_stock_date", "design_id", "stock_date")

    # === Step 3: CREATE 3 line tables (FK children) ===
    op.create_table(
        "tbl_inward_line",
        sa.Column("line_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("header_id", sa.BigInteger(), nullable=False),
        sa.Column("design_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column("nos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["header_id"], ["tbl_inward_header.header_id"], name="fk_inward_line_header_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["design_id"], ["tbl_trading_design_master.design_id"], name="fk_inward_line_design_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grade_id"], ["tbl_grade_master.grade_id"], name="fk_inward_line_grade_id", ondelete="RESTRICT"),
        sa.CheckConstraint("nos > 0", name="ck_inward_line_nos_positive"),
    )
    op.create_index("ix_inward_line_header", "tbl_inward_line", ["header_id"])
    op.create_index("ix_inward_line_dgd", "tbl_inward_line", ["design_id", "grade_id", "header_id"])

    # tbl_sales_line — same pattern with FK to tbl_sales_header, CHECK(nos > 0), ix_sales_line_dgd.

    # tbl_adjustment_line — FK to tbl_adjustment_header (CASCADE), grade_id FK to tbl_grade_master (RESTRICT),
    #   software_cb INTEGER NOT NULL, physical_cb INTEGER NOT NULL with CHECK(>=0), difference INTEGER NOT NULL.

    # === Step 4: CREATE tbl_stock_ledger ===
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
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["design_id"], ["tbl_trading_design_master.design_id"], name="fk_stock_ledger_design_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grade_id"], ["tbl_grade_master.grade_id"], name="fk_stock_ledger_grade_id", ondelete="RESTRICT"),
        sa.CheckConstraint("source_type IN ('inward', 'sale', 'adjustment')", name="ck_stock_ledger_source_type"),
    )
    op.execute(
        "CREATE INDEX ix_stock_ledger_dgt ON tbl_stock_ledger "
        "(design_id, grade_id, txn_date DESC, ledger_id DESC)"
    )


def downgrade() -> None:
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
    op.drop_index("ix_adjustment_header_design_stock_date", table_name="tbl_adjustment_header")
    op.drop_table("tbl_adjustment_header")
    op.drop_index("ix_sales_header_dealer", table_name="tbl_sales_header")
    op.drop_index("ix_sales_header_sales_date", table_name="tbl_sales_header")
    op.drop_table("tbl_sales_header")
    op.drop_index("ix_inward_header_purchase_date", table_name="tbl_inward_header")
    op.drop_table("tbl_inward_header")
    # Revert TIMESTAMPTZ on 4 S1 columns.
    for table in (
        "tbl_supplier_master", "tbl_staff_master", "tbl_dealer_master", "tbl_trading_design_master",
    ):
        op.alter_column(
            table, "created_at",
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("now()"),
        )
```

## Constraints
- DS-009: ORM (T-042) is the canonical source; this migration mirrors `Base.metadata` exactly.
- DS-014: ALTERs land in this migration alongside the new-table creates so the schema becomes uniform in one step.
- Constraint names match the ORM (`ck_*_nos_positive`, `ck_stock_ledger_source_type`, `ck_adjustment_header_dates`, `ck_adjustment_line_physical_cb_nonneg`). TC-053/064/069/088/089 assert against these names.
- Drop order in downgrade: indexes → child tables (lines) → parent tables (headers) → stock_ledger separate → ALTER reverts last.

## Step 4.5 — Apply migration

The /ases-dev skill's Step 4.5 says to run `psql ... -f <sql>` for `.sql` migrations. This is a `.py` Alembic migration → apply via `alembic upgrade head` instead. Without W5 closed locally, an IS-002-pattern test-time apply against a testcontainer PG is the verification path.

## Do not touch
Any other file. Do not modify `0002_master_tables.py`.

## Success criteria
- **Manual:** `alembic upgrade head` succeeds; `\d tbl_inward_line` shows `ck_inward_line_nos_positive`; `\d tbl_stock_ledger` shows `ck_stock_ledger_source_type` + `ix_stock_ledger_dgt`.
- **Automated:** TC-053, TC-064, TC-069, TC-088, TC-089 all raise `IntegrityError` referring to the expected constraint names.
- **DoD:** Revision id `'0003_transaction_and_ledger_tables'` is stable; downgrade round-trip works; ix_stock_ledger_dgt exists.

## Checkout prompt
*"Migration 0003 — 4 ALTERs + 7 new tables + composite index. alembic upgrade head clean."*
