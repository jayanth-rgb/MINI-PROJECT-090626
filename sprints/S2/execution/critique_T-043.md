# Critique — T-043 Transaction + StockLedger repositories

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/infrastructure/db/repositories/transactions.py` (119 lines, 4 classes, 8 methods)

## Decisions referenced (read first)
- **DS-002** — SELECT FOR UPDATE on latest (design_id, grade_id) row before write ✓
- **DS-003** — Materialized `running_balance`; `rows_after()` drives bounded forward-recompute ✓
- **DS-012** — Generic BaseRepository[TModel] subclassed per entity ✓

## Lens 1 — Spec

### Class roster vs plan.json / LLD `files[3]`
| Class | Base | Added method(s) | Match |
|---|---|---|---|
| InwardHeaderRepository | BaseRepository[InwardHeaderModel] | create_with_lines | ✓ |
| SalesHeaderRepository | BaseRepository[SalesHeaderModel] | create_with_lines | ✓ |
| AdjustmentHeaderRepository | BaseRepository[AdjustmentHeaderModel] | create_with_lines (filled in from plan.md `...` placeholder by mirroring) | ✓ |
| StockLedgerRepository | BaseRepository[StockLedgerModel] | latest_for_design_grade, latest_as_of, rows_after, insert | ✓ |

### Method signature cross-check (LLD `files[3].functions[]`)
- `latest_for_design_grade(design_id: int, grade_id: int, for_update: bool = False) → StockLedgerModel | None` ✓
- `latest_as_of(design_id: int, grade_id: int, as_of_date: date) → StockLedgerModel | None` ✓
- `rows_after(design_id: int, grade_id: int, after_date_inclusive: date) → list[StockLedgerModel]` ✓
- `insert(data: dict) → StockLedgerModel` — LLD structured type is `dict[str, Any]`; plan.md uses plain `dict`. Runtime-equivalent; plan.md is the implementation SoT for `/ases-dev`. Not a finding.

### Query construction
- `latest_for_design_grade`: `ORDER BY txn_date DESC, ledger_id DESC LIMIT 1` — matches `ix_stock_ledger_dgt` composite index from T-042 ✓
- `latest_as_of`: same ordering + `txn_date <= as_of_date` filter ✓
- `rows_after`: ASC ordering + `txn_date >= after_date_inclusive` filter — bounded by AC-021's 7-day window per DS-003 ✓
- `with_for_update()` applied iff `for_update=True` — DS-002 lock acquisition gated by caller ✓
- All methods use `session.flush()` (no commit) — caller commits per the service-transaction boundary ✓

### `create_with_lines` pattern
- Pattern: `add(header) → flush (assigns PK) → loop add lines with header_id → flush → return header`
- AC-027 atomicity: caller wraps in a transaction; partial-write failure rolls everything back ✓
- AdjustmentLine has no `design_id` (header owns it per AC-034); `**lp` unpacks the AdjustmentLineModel-specific fields (grade_id, software_cb, physical_cb, difference) without leakage ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports` = 4 class names — all 4 declared at module level ✓

### Expects
LLD `interfaces.expects` = `["BaseRepository", "7 ORM models from models/transactions.py"]`
- `BaseRepository` imported from `repositories/base.py` ✓
- All 7 ORM models imported (Inward/Sales/Adjustment Header + Line × 3 + StockLedgerModel) ✓

### Imports vs depends_on[]
- `backend/src/infrastructure/db/repositories/base.py` → imported ✓
- `backend/src/infrastructure/db/models/transactions.py` → imported ✓

### Dead-code scan
- `date` used in `latest_as_of` + `rows_after` type hints ✓
- `select` used in 3 query builders ✓
- All 6 line/header ORM model imports used in `create_with_lines` instantiation or repo binding ✓
- `StockLedgerModel` used in 4 method bodies + class binding ✓
No unused imports.

## Lens 3 — Test

T-043 has `test_case_refs = []`. Verified transitive coverage via T-045 domain TCs that exercise these repository methods:

| TC | Method exercised | Status |
|---|---|---|
| TC-079 closing_balance happy path | `latest_as_of` returns the row with txn_date ≤ as_of | ✓ |
| TC-080 closing_balance no rows = 0 | `latest_as_of` returns `None` on empty; domain handles None→0 | ✓ |
| TC-081 opening_balance = closing(month_first − 1) | reuses `latest_as_of` | ✓ |
| TC-082 first-month opening = 0 | same as TC-080 | ✓ |
| TC-083 apply_inward delta=+nos | `latest_for_design_grade(for_update=True)` + `insert` | ✓ |
| TC-084 apply_sale delta=−nos | same path | ✓ |
| TC-085 apply_adjustment delta=difference | same path | ✓ |
| TC-086 back-dated forward-recompute | `rows_after(after_date_inclusive)` | ✓ |
| TC-087 concurrent SAVEs serialize | `with_for_update()` emits `SELECT … FOR UPDATE` (PG) | ✓ |

All 9 transitive TC paths are wired at the repository layer; T-045 domain will compose them.

## Lens 4 — Security

- No raw SQL — all queries use SQLAlchemy expression API (parameterized binds) ✓
- `**header_payload` and `**lp` unpacking is bounded by ORM column allow-list — SQLAlchemy raises `TypeError` on unknown kwargs ✓
- Trust boundary: per DS-007, presentation layer (Pydantic) validates upstream; infrastructure layer trusts validated dicts. Acceptable.
- No exposed secrets, credentials, or PII in this file.
- `with_for_update()` is the only locking primitive — does not bypass FK/CHECK constraints from T-042.

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists (8442 nodes / 8939 edges, S2-scaffold snapshot).

- New file currently orphaned in live call graph — downstream consumers land in T-045 (domain), T-047/048/049 (services), T-050 (design_grade_cb_service). This is the documented two-step dependency chain.
- BaseRepository import edge resolves to the S1 `repositories/base.py` — the `__class_getitem__` dynamic-subclass trick (DS-012) verified to work with SQLAlchemy 2.x ORM registry in S1's master entity tests.
- ORM model edges to `models/transactions.py` (T-042) are intact.
- No dead imports; no shadowed names; no circular imports (`models/transactions.py` does not import from `repositories/`).

Not critique-blocking.

## Verdict

**CLEAN** — 4 repositories written exactly to spec. DS-002 lock semantics (`with_for_update()` conditional on `for_update=True`), DS-003 materialized read paths (`latest_as_of` + `rows_after`), and DS-012 BaseRepository pattern all correctly applied. 9 transitive TCs (TC-079..TC-087) wired for T-045 domain implementation.

→ Update `tasks.json` T-043 status to `complete`, advance context. Next per execution_order: T-044 (migration 0003 — depends on T-041 + T-042; T-043 not blocking) or T-045 (domain stock — depends on T-043 complete, NOW UNBLOCKED) or T-046 (Pydantic schemas, parallel group A still open).
