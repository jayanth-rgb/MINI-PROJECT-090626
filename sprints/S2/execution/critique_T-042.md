# Critique — T-042 Transaction + Stock Ledger ORM models

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/infrastructure/db/models/transactions.py` (244 lines, 7 model classes)

## Decisions referenced (read first)
- **DS-007** — Layer purity: ORM models in infrastructure only, no business logic ✓
- **DS-008** — Soft-delete: N/A for tx tables (master-layer concern)
- **DS-009** — ORM-first: this file is the source-of-truth for T-044 migration ✓
- **DS-013** — Denormalize `place` on Inward + Sales headers ✓
- **DS-014** — TIMESTAMPTZ via TimestampMixin (inherited from T-041) ✓

## Lens 1 — Spec

### Class roster
All 7 model classes present and inheriting correctly:
| Class | Inherits | Reason |
|---|---|---|
| InwardHeaderModel | (Base, TimestampMixin) | header → needs created_at TIMESTAMPTZ ✓ |
| InwardLineModel | (Base,) | line → no created_at ✓ |
| SalesHeaderModel | (Base, TimestampMixin) | header ✓ |
| SalesLineModel | (Base,) | line ✓ |
| AdjustmentHeaderModel | (Base, TimestampMixin) | header ✓ |
| AdjustmentLineModel | (Base,) | line ✓ |
| StockLedgerModel | (Base, TimestampMixin) | ledger row also stamps created_at per schema field ✓ |

### Column-level cross-check vs schema.json
- **InwardHeader**: header_id BIGSERIAL PK, purchase_date DATE, supplier_id FK→supplier RESTRICT, place TEXT (DS-013), entered_by_id FK→staff RESTRICT, created_at TIMESTAMPTZ ✓
- **InwardLine**: line_id, header_id FK→inward_header CASCADE, design_id FK→design RESTRICT, grade_id FK→grade RESTRICT, nos INTEGER ✓
- **SalesHeader**: header_id, sales_date, dealer_id RESTRICT, place TEXT (DS-013), loading_staff_id RESTRICT, verified_by_id RESTRICT, created_at TIMESTAMPTZ ✓
- **SalesLine**: mirror of InwardLine with FK→sales_header CASCADE ✓
- **AdjustmentHeader**: header_id, stock_date, entry_date, design_id RESTRICT (AC-034 — design on header, not line), entered_by_id RESTRICT, created_at TIMESTAMPTZ ✓
- **AdjustmentLine**: line_id, header_id FK→adjustment_header CASCADE, grade_id RESTRICT, software_cb INTEGER, physical_cb INTEGER, difference INTEGER (persisted not GENERATED per DS-003) ✓
- **StockLedger**: ledger_id, design_id RESTRICT, grade_id RESTRICT, txn_date DATE, source_type TEXT, source_header_id BIGINT NULL, source_line_id BIGINT NULL, delta INTEGER, running_balance INTEGER, created_at TIMESTAMPTZ ✓

### CHECK constraints — names match schema verbatim
- `ck_inward_line_nos_positive` (nos > 0) ✓
- `ck_sales_line_nos_positive` (nos > 0) ✓
- `ck_adjustment_header_dates` (stock_date <= entry_date) — backstops AC-035 / ERR-010 ✓
- `ck_adjustment_line_physical_cb_nonneg` (physical_cb >= 0) — AC-037 ✓
- `ck_stock_ledger_source_type` (IN list) ✓

### Indexes — 9 declared, all schema-aligned
- ix_inward_header_purchase_date ✓
- ix_inward_line_header, ix_inward_line_dgd ✓
- ix_sales_header_sales_date, ix_sales_header_dealer ✓
- ix_sales_line_header, ix_sales_line_dgd ✓
- ix_adjustment_header_design_stock_date ✓
- ix_adjustment_line_header ✓
- **ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)** — uses `text("txn_date DESC")` and `text("ledger_id DESC")` per plan.md ✓

### Relationships
- Header→lines (one-to-many, cascade='all, delete-orphan', lazy='joined') configured for all 3 headers ✓
- Line→design/grade relationships **not added**. Defensible: LLD `interfaces.exports` lists only 7 model classes; LLD function descriptions for line models do not mention these relationship attributes; plan.md DoD hedges with *"where needed for hydrated reads"*. Services in T-047/048/049 can hydrate via explicit query or the relationships can be added when actually exercised. Not a critique finding — recorded for transparency.

## Lens 2 — Contract

### Exports
LLD `interfaces.exports` = 7 class names — all 7 are exported at module level ✓
Class names match exactly (case + spelling) ✓

### Expects
LLD `interfaces.expects` = `["Base", "TimestampMixin (with TIMESTAMPTZ per DS-014)"]`
- `from src.infrastructure.db.base import Base, TimestampMixin` ✓
- TimestampMixin emits `DateTime(timezone=True)` post-T-041 (verified) ✓

### Imports vs depends_on[]
- `backend/src/infrastructure/db/base.py` → imported correctly ✓
- `sprints/S2/design/schema.json` → reference doc, not imported (correct) ✓

### Naming + style
- `__tablename__` matches schema entity name for all 7 ✓
- BigInteger autoincrement → maps to PG BIGSERIAL ✓ (matches S1 master.py style verbatim)
- `text()` import correctly used inside Index for DESC ordering ✓

## Lens 3 — Test

T-042 has `test_case_refs = []`. Verified transitive coverage via T-044 migration TCs that exercise these constraints:

| TC | Constraint | Status |
|---|---|---|
| TC-053 | tbl_inward_line CHECK(nos > 0) | satisfied by `ck_inward_line_nos_positive` ✓ |
| TC-064 | tbl_sales_line CHECK(nos > 0) | satisfied by `ck_sales_line_nos_positive` ✓ |
| TC-069 | tbl_adjustment_header CHECK(stock_date <= entry_date) | satisfied by `ck_adjustment_header_dates` ✓ |
| TC-088 | tbl_stock_ledger CHECK(source_type IN …) | satisfied by `ck_stock_ledger_source_type` ✓ |
| TC-089 | FK RESTRICT on tbl_inward_header.supplier_id | satisfied by `ondelete="RESTRICT"` ✓ |

All five expected `sqlalchemy.exc.IntegrityError` paths are wired at the ORM level; T-044 migration will materialize them as DB constraints.

## Lens 4 — Security

- No user input flows through this file (pure ORM declarations).
- `text()` arguments are literal string constants ("txn_date DESC", "ledger_id DESC") — no concatenation, no injection vector.
- CHECK constraint SQL uses literal values from schema spec — safe.
- FK `ondelete=RESTRICT` on master refs prevents accidental data loss (mirrors DS-008 invariant at DB level).
- FK `ondelete=CASCADE` on line→header is intentional and scoped to one transactional unit per AC-027 atomicity contract.
- No secrets, no credentials, no I/O.

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists (8442 nodes / 8939 edges, post-S2-scaffold snapshot).

- New file `backend/src/infrastructure/db/models/transactions.py` is currently orphaned in the call graph — that's the documented two-step dependency: T-043 (repositories) imports the 7 classes, T-044 (migration) references the table metadata, T-047/048/049 (services) compose them via the repository layer.
- TimestampMixin edge to `base.py` is intact (post-T-041 ORM upgrade).
- FK strings reference 5 S1 tables — all present in `master.py`: `tbl_supplier_master`, `tbl_staff_master`, `tbl_dealer_master`, `tbl_trading_design_master`, `tbl_grade_master` ✓
- Forward-reference relationship strings (`"InwardLineModel"`, `"SalesLineModel"`, `"AdjustmentLineModel"`) resolve within the same module — SQLAlchemy lazy-resolves these on registry construction; no risk of `KeyError` at import time.
- No dead imports: every name in the `sqlalchemy` import block (`BigInteger`, `CheckConstraint`, `Date`, `ForeignKey`, `Index`, `Integer`, `Text`, `text`) is used at least once.

Not critique-blocking.

## Verdict

**CLEAN** — 7 ORM models written exactly to spec. All CHECK + FK + index naming matches schema.json verbatim. DS-013 denormalization, DS-014 TIMESTAMPTZ inheritance, and DS-003 materialized `running_balance` all correctly modeled. Five transitive CHECK/FK TCs (TC-053/064/069/088/089) wired for T-044 migration verification.

→ Update `tasks.json` T-042 status to `complete`, advance context. Next per execution_order: T-043 (repositories) or T-044 (migration) — both depend on T-042 complete.
