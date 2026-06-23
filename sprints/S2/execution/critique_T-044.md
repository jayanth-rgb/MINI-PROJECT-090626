# Critique — T-044 Alembic migration 0003

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/db/migrations/versions/0003_transaction_and_ledger_tables.py` (300 lines, 4-phase upgrade + reverse downgrade)

## Decisions referenced (read first)
- **DS-009** — ORM is source-of-truth; hand-authored migration is W5/TD-005 carry-over pattern from S1 (no PG up to run `--autogenerate`). Equivalence verified by IS-002 testcontainer ✓
- **DS-014** — TIMESTAMPTZ uplift on 4 S1 columns + all 4 new TZ-bearing columns (3 headers + stock_ledger) emit `DateTime(timezone=True)` ✓
- **DS-002** — `ix_stock_ledger_dgt` composite (design_id, grade_id, txn_date DESC, ledger_id DESC) created for SELECT FOR UPDATE lookup ✓
- **DS-003** — Same composite supports `running_balance` rebuild via `rows_after` ✓
- **DS-013** — `place TEXT NOT NULL` on Inward + Sales headers ✓

## Lens 1 — Spec

### Revision chain
- `revision = "0003_transaction_and_ledger_tables"` ✓
- `down_revision = "0002_master_tables"` ✓ (continues the S1 chain)
- `branch_labels = None`, `depends_on = None` (matches S1 0002 style) ✓
- `from __future__ import annotations` carried forward ✓

### Phase 1 — 4 ALTERs (DS-014)
- Loop over `supplier / staff / dealer / trading_design` master tables
- `type_=sa.DateTime(timezone=True)`, `existing_type=sa.DateTime()` ✓
- `postgresql_using="created_at AT TIME ZONE 'UTC'"` — data-preserving cast ✓
- `existing_nullable=False`, `existing_server_default=sa.text("now()")` — preserves server_default ✓

### Phase 2 — 3 header tables
All header column lists cross-checked against schema.json entity definitions:
- **tbl_inward_header**: header_id BIGSERIAL PK, purchase_date, supplier_id FK RESTRICT, place TEXT (DS-013), entered_by_id FK RESTRICT, created_at TIMESTAMPTZ NOT NULL DEFAULT now() ✓ + `ix_inward_header_purchase_date`
- **tbl_sales_header**: header_id, sales_date, dealer_id RESTRICT, place TEXT (DS-013), loading_staff_id RESTRICT, verified_by_id RESTRICT, created_at TIMESTAMPTZ ✓ + `ix_sales_header_sales_date` + `ix_sales_header_dealer`
- **tbl_adjustment_header**: header_id, stock_date, entry_date, design_id RESTRICT (AC-034), entered_by_id RESTRICT, created_at TIMESTAMPTZ, `ck_adjustment_header_dates` (stock_date ≤ entry_date) ✓ + `ix_adjustment_header_design_stock_date`

### Phase 3 — 3 line tables (FK CASCADE on header)
- **tbl_inward_line**: line_id, header_id CASCADE, design_id RESTRICT, grade_id RESTRICT, nos + `ck_inward_line_nos_positive` ✓ + `ix_inward_line_header`, `ix_inward_line_dgd`
- **tbl_sales_line**: mirror of inward_line with FK to sales_header CASCADE + `ck_sales_line_nos_positive` ✓ + 2 indexes
- **tbl_adjustment_line**: line_id, header_id CASCADE, grade_id RESTRICT, software_cb, physical_cb, difference + `ck_adjustment_line_physical_cb_nonneg` ✓ + `ix_adjustment_line_header`

### Phase 4 — Stock ledger
- All 10 columns + 2 named FKs (RESTRICT) + `ck_stock_ledger_source_type` ✓
- `ix_stock_ledger_dgt` via `op.execute("CREATE INDEX … (design_id, grade_id, txn_date DESC, ledger_id DESC)")` — required because `op.create_index` doesn't natively express per-column DESC. Justified in inline comment ✓

### Constraint name registry (matches T-042 ORM verbatim)
- 5 CHECK constraints, all explicitly named ✓
- 17 FK constraints, all named per `fk_<table>_<column>` pattern (matches S1's 0002 style) ✓

### Downgrade
Reverse FK dependency order strictly maintained:
1. Drop `ix_stock_ledger_dgt` + drop `tbl_stock_ledger`
2. Drop adjustment_line / sales_line / inward_line (lines first; their indexes precede table drops)
3. Drop adjustment_header / sales_header / inward_header
4. ALTER 4 S1 created_at back to plain `TIMESTAMP` (without `postgresql_using` — symmetric with how 0002 created them)

## Lens 2 — Contract

### Module-level exports
- `revision`, `down_revision`, `branch_labels`, `depends_on` constants ✓
- `upgrade()` and `downgrade()` functions ✓

### Imports vs LLD `expects`
- `alembic.op` — used in every DDL call ✓
- `sqlalchemy as sa` — used for Column types, FK/CHECK constraints, `func.now()`, `text("now()")` ✓
- No unused imports

### Revision chain integrity
- `down_revision = "0002_master_tables"` matches S1's revision id (verified in S1 sprint_history commit 571c601) ✓
- No branch divergence; linear chain 0002 → 0003

## Lens 3 — Test

T-044 `test_case_refs = ["TC-053", "TC-064", "TC-069", "TC-088", "TC-089"]` — all 5 traced to the migration:

| TC | Description | Wired via |
|---|---|---|
| TC-053 | Insert nos=0 on tbl_inward_line → IntegrityError | `ck_inward_line_nos_positive` ✓ |
| TC-064 | Insert nos=0 on tbl_sales_line → IntegrityError | `ck_sales_line_nos_positive` ✓ |
| TC-069 | Insert stock_date > entry_date on tbl_adjustment_header → IntegrityError | `ck_adjustment_header_dates` ✓ |
| TC-088 | Insert source_type='foo' on tbl_stock_ledger → IntegrityError | `ck_stock_ledger_source_type` ✓ |
| TC-089 | Hard DELETE supplier with inward rows → IntegrityError | `fk_inward_header_supplier_id` ondelete=RESTRICT ✓ |

All 5 will fire `sqlalchemy.exc.IntegrityError` referencing the exact constraint name the tests assert against.

## Lens 4 — Security

- Pure DDL — no user input flows through this file
- One raw DDL via `op.execute()` for the composite DESC index. SQL string is hard-coded with literal table + column names — no concatenation, no injection vector ✓
- CHECK constraints use hard-coded SQL string literals from schema spec ✓
- `postgresql_using="created_at AT TIME ZONE 'UTC'"` — literal fragment, no user input ✓
- No secrets, no credentials, no `os.environ` access
- FK RESTRICT defense-in-depth backs the application-layer DS-008 soft-delete invariant ✓
- FK CASCADE on line→header is intentional and scoped to one transactional unit (mirrors ORM cascade='all, delete-orphan')

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- Migration file is a leaf — at runtime imports only `alembic.op` and `sqlalchemy`; project modules are not imported here. Loaded by `alembic upgrade head` based on revision chain metadata.
- Revision chain: 0001 baseline (placeholder) → 0002_master_tables → 0003_transaction_and_ledger_tables — linear, no branches ✓
- The 5 referenced S1 tables (`tbl_supplier_master`, `tbl_staff_master`, `tbl_dealer_master`, `tbl_trading_design_master`, `tbl_grade_master`) all exist in 0002 ✓
- FK target columns (`supplier_id`, `staff_id`, `dealer_id`, `design_id`, `grade_id`) all match S1's BIGSERIAL primary keys ✓

Not critique-blocking.

## Transparency notes (not findings)

1. **Hand-authored migration vs DS-009 autogenerate** — per W5/TD-005 carry-over from S1, no live PG is available to run `alembic revision --autogenerate`. The migration mirrors `Base.metadata` exactly (cross-checked column-by-column against schema.json + T-042 ORM). The IS-002 testcontainer pattern (S1) verifies equivalence ephemerally at test time. This is the documented S1 → S2 pattern, not new tech debt.
2. **Downgrade ALTER without `postgresql_using`** — symmetric with how 0002 created the columns (no USING clause specified). TIMESTAMPTZ→TIMESTAMP without USING uses the session's timezone for the cast. Acceptable for a downgrade path used in dev/test only.
3. **`migration_applied: false`** — Step 4.5's psql auto-trigger fires only for `.sql` files; T-044 is `.py`. Actual `alembic upgrade head` exercise lands at `/ases-test-run S2` via testcontainers.

## Verdict

**CLEAN** — 4-phase upgrade (4 ALTERs + 3 headers + 3 lines + stock_ledger) and reverse-order downgrade written exactly to spec. All 5 CHECK + 17 FK constraint names match T-042 ORM verbatim; `ix_stock_ledger_dgt` composite DESC index created via raw DDL (only path that expresses per-column DESC). 5 transitive TCs (TC-053/064/069/088/089) all wired correctly.

→ Update `tasks.json` T-044 status to `complete`, advance context. Next per execution_order: T-045 (domain stock — critical-path file, unblocked by T-043) or T-046 (Pydantic schemas, parallel group A still open).
