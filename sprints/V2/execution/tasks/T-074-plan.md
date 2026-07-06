# T-074 — `db/migrations/versions/0004_v2_auth_pricing_tables.py` — Alembic migration

**Module:** M-008 · **Wave:** 2 (after T-067 + T-079) · **Depends on:** T-067 (UserModel), T-079 (pricing models)

## Context anchor

Continues the migration chain: 0001_baseline.sql → 0002_master_tables.py → 0003_transaction_and_ledger_tables.py → **0004_v2_auth_pricing_tables.py** (this task). Per DS-009 (ORM-first), generate from `alembic revision --autogenerate` then manually add CHECK constraints that autogenerate misses.

## Implementation logic

Key DDL (illustrative — use autogenerate then patch):

```python
# Revision: 0004 | Down: 0003

def upgrade() -> None:
    # tbl_user_master
    op.create_table(
        "tbl_user_master",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("username"),
        sa.CheckConstraint("role IN ('STAFF','VERIFIER','SUPERVISOR')", name="ck_user_role"),
    )
    op.create_index("ix_user_master_username", "tbl_user_master", ["username"])

    # tbl_price_master
    op.create_table(
        "tbl_price_master",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("design_id", sa.Integer, sa.ForeignKey("tbl_trading_design_master.id"), nullable=False),
        sa.Column("grade_id", sa.Integer, sa.ForeignKey("tbl_grade_master.id"), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("design_id", "grade_id", "effective_from",
                            name="uq_price_design_grade_effective"),
        sa.CheckConstraint("unit_price >= 0", name="ck_price_unit_price_nonneg"),
    )

    # tbl_invoice_header
    op.create_table(
        "tbl_invoice_header",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("invoice_number", sa.String(30), unique=True, nullable=False),
        sa.Column("sales_header_id", sa.Integer, sa.ForeignKey("tbl_sales_header.id"),
                  unique=True, nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(10), default="PENDING", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING','PARTIAL','PAID')", name="ck_invoice_status"),
    )

    # tbl_invoice_line
    op.create_table(
        "tbl_invoice_line",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("invoice_header_id", sa.Integer,
                  sa.ForeignKey("tbl_invoice_header.id"), nullable=False),
        sa.Column("sales_line_id", sa.Integer,
                  sa.ForeignKey("tbl_sales_line.id"), unique=True, nullable=False),
        sa.Column("design_id", sa.Integer, nullable=False),
        sa.Column("grade_id", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # tbl_payment
    op.create_table(
        "tbl_payment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("invoice_header_id", sa.Integer,
                  sa.ForeignKey("tbl_invoice_header.id"), nullable=False),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )


def downgrade() -> None:
    op.drop_table("tbl_payment")
    op.drop_table("tbl_invoice_line")
    op.drop_table("tbl_invoice_header")
    op.drop_table("tbl_price_master")
    op.drop_index("ix_user_master_username", table_name="tbl_user_master")
    op.drop_table("tbl_user_master")
```

## Constraints

- `down_revision` must be `'0003'` — the transaction/ledger migration.
- CHECK constraints (`ck_user_role`, `ck_invoice_status`, `ck_payment_amount_positive`, `ck_price_unit_price_nonneg`) must be added **manually** — `alembic --autogenerate` does not emit them for inline CHECK.
- `downgrade()` drops tables in reverse FK order: `tbl_payment` before `tbl_invoice_line` before `tbl_invoice_header`. `tbl_user_master` last (no FK dependencies).
- The Enum for `role` in `UserModel` may generate a PostgreSQL `CREATE TYPE` — if so, `upgrade()` creates the type before the table; `downgrade()` drops the type after the table.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `cd backend && alembic upgrade head && alembic current` → head at `0004`.
- **Automated**: Integration test fixtures call `alembic upgrade head` via `alembic.command.upgrade(alembic_cfg, 'head')` in conftest.py.
- **DoD**: Migration file exists. down_revision='0003'. upgrade() creates 5 tables with all constraints. downgrade() reverses completely.

## Checkout

> *"Migration 0004 created. 5 tables: tbl_user_master, tbl_price_master, tbl_invoice_header, tbl_invoice_line, tbl_payment. All constraints included. Chains to 0003."*
