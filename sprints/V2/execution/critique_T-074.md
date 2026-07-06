# Critique — T-074 · Migration 0004 V2 Auth + Pricing Tables

**Sprint:** V2 · **Iteration:** 2 · **Verdict:** ✅ CLEAN  
**Reviewed:** 2026-07-04 · **Reviewer:** /ases-critique  
**File:** `backend/db/migrations/versions/0004_v2_auth_pricing_tables.py`

---

## Verdict Summary

| Severity | Count | Genuine | ADR Tradeoff |
|----------|-------|---------|--------------|
| Critical | 0 | 0 | 0 |
| Major    | 0 | 0 | 0 |
| Minor    | 2 | 0 | 2 |

**CLEAN — no genuine issues. Both observations are ADR tradeoffs per DS-009 (ORM-first).**

---

## Lens 1 — Spec

### I-001 · Minor · ADR Tradeoff

**Observation:** LLD `upgrade()` prose specifies `role VARCHAR(20) NOT NULL CHECK(role IN ('STAFF','VERIFIER','SUPERVISOR'))`, but the migration uses a PostgreSQL named ENUM type (`user_role_enum`). The LLD's ORM model description for `auth.py` correctly specifies `Enum('STAFF','VERIFIER','SUPERVISOR')` — creating an internal contradiction in the LLD itself.

**Resolution:** Migration correctly follows the ORM model per **DS-009** (ORM-first). The code comment on lines 17–18 documents this rationale explicitly. The LLD `upgrade()` prose description is the inaccuracy. **No fix required.**

**ADR Ref:** DS-009

---

### I-002 · Minor · ADR Tradeoff

**Observation:** `tbl_user_master.username` has BOTH a column-level `unique=True` (backed by a PostgreSQL unique B-tree index) AND a separate `op.create_index("ix_user_master_username", ...)` (a non-unique index on the same column). The separate non-unique index is redundant — the unique constraint's backing index already covers all lookup paths. This adds storage overhead and a write penalty with no query benefit.

**Resolution:** The migration correctly mirrors the ORM model's `__table_args__` (`Index("ix_user_master_username", "username")` coexisting with `unique=True` on the column) per **DS-009**. The source of redundancy is in the ORM model design; eliminating it requires editing `UserModel.__table_args__` and regenerating the migration — out of T-074 scope. **No fix required for T-074.**

**ADR Ref:** DS-009

---

## Lens 2 — Contract

All FK references verified against prior migrations:

| FK Column | Implementation | Verified Against | Result |
|-----------|---------------|-----------------|--------|
| `tbl_price_master.design_id` | `BigInteger → tbl_trading_design_master.design_id` | 0002 migration PK | ✅ Correct |
| `tbl_price_master.grade_id` | `BigInteger → tbl_grade_master.grade_id` | 0002 migration PK | ✅ Correct |
| `tbl_invoice_header.sales_header_id` | `BigInteger → tbl_sales_header.header_id` | 0003 migration PK | ✅ Correct |
| `tbl_invoice_line.sales_line_id` | `BigInteger → tbl_sales_line.line_id` | 0003 migration PK | ✅ Correct |
| `tbl_invoice_line.invoice_header_id` | `Integer → tbl_invoice_header.id` | Same migration | ✅ Correct |
| `tbl_payment.invoice_header_id` | `Integer → tbl_invoice_header.id` | Same migration | ✅ Correct |

Revision chain: `down_revision = "0003_tx_ledger"` matches `revision = "0003_tx_ledger"` in the 0003 migration. ✅

ENUM type (`user_role_enum`) matches the ORM model `UserModel.role` definition exactly. ✅

`tbl_invoice_line.design_id` and `grade_id` are plain `Integer` (no FK) — correct for denormalized snapshots per **DS-022**. ✅

---

## Lens 3 — Test

`test_case_refs: []` — no automated test cases for this task. Success criteria is `alembic upgrade head → no error` (manual) and the integration test fixture running `alembic upgrade head` (automated path via other TCs). Migration DDL is syntactically valid. ✅

---

## Lens 4 — Security

- `password_hash VARCHAR(255)` — appropriate sizing for bcrypt output (60 chars); 255 gives headroom for future algorithms. ✅
- No secrets, credentials, or hardcoded values in the migration file. ✅
- `CHECK(amount > 0)` on `tbl_payment.amount` prevents zero/negative payment records. ✅
- `CHECK(unit_price >= 0)` on `tbl_price_master` prevents negative pricing. ✅
- `CHECK(status IN ('PENDING','PARTIAL','PAID'))` on `tbl_invoice_header` constrains status at DB level per DS-023. ✅
- ENUM type for role (vs VARCHAR + CHECK) provides slightly stronger type enforcement at the PostgreSQL level. ✅

---

## Validated Correct (Summary)

- All 5 tables created: `tbl_user_master`, `tbl_price_master`, `tbl_invoice_header`, `tbl_invoice_line`, `tbl_payment`
- All UNIQUE constraints present: `username`, `uq_price_design_grade_effective`, `invoice_number`, `UNIQUE(sales_header_id)`, `UNIQUE(sales_line_id)`
- All CHECK constraints present per plan scope
- `created_at` uses `DateTime(timezone=True)` on all tables per DS-014
- `downgrade()` drops tables in correct reverse-dependency order, then drops `user_role_enum`
- ENUM type creation handled implicitly by Alembic `op.create_table()` (standard PostgreSQL dialect behavior)

---

## Iteration Note

Iteration 2 re-confirms the iteration 1 CLEAN verdict. Code is unchanged. The `tasks.json` `status=complete` update was not applied after iteration 1; this run triggers it.

## Action

**CLEAN → T-074 status = `complete`**  
Next: proceed per execution wave order.
