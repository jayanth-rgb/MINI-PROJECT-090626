# Critique — T-059 (iteration 1)

**Task:** LedgerAggregatesRepository — single CASE-aggregated GROUP BY
**File:** `backend/src/infrastructure/db/repositories/ledger_aggregates.py`
**Module:** M-004
**ADR anchor:** DS-016 (single CASE-aggregated GROUP BY for dashboard)
**Verdict:** CLEAN

## Load-bearing property verification

| # | Property | Status | Evidence |
|---|---|---|---|
| 1 | SINGLE SQL statement (no N+1) | PASS | One `self.session.execute(stmt).all()` at line 79; no per-pair loops |
| 2 | `outward_sum` reads positive | PASS | Line 60: `case((source_type == "sale", -StockLedgerModel.delta), else_=0)` — negates the stored negative `delta` |
| 3 | `func.coalesce(..., 0)` on all three SUMs | PASS | inward_sum line 48, outward_sum line 57, adjust_sum line 66 — all three wrapped |
| 4 | Date window inclusive on both ends | PASS | Line 76: `txn_date.between(month_start, as_of_date)` — SQLAlchemy `between()` emits SQL `BETWEEN ... AND ...`, inclusive both ends; matches AC-053 |
| 5 | GROUP BY (design_id, grade_id) prefix aligns with ix_stock_ledger_dgt | PASS | Line 77: `group_by(design_id, grade_id)` matches the leading columns of `ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)` per S2 models/transactions.py:254-260; planner can use Index Range Scan |

## 5-lens analysis

### Lens 1 — Spec
- Method signature `sum_deltas_by_source_type(month_start: date, as_of_date: date) -> list[Row]` exactly matches LLD files[1].functions[0] (inputs + outputs).
- Class is `LedgerAggregatesRepository(BaseRepository[StockLedgerModel])` per LLD spec.
- Behaviour matches LLD description: CASE-aggregated SUMs over `tbl_stock_ledger` with `txn_date BETWEEN :month_start AND :as_of_date`, GROUP BY (design_id, grade_id), one row per pair with `design_id, grade_id, inward_sum, outward_sum, adjust_sum` (outward = sum of -delta for sales so it reads positive).
- DS-016 referenced in module docstring (lines 1-9) and method docstring (line 41).

### Lens 2 — Contract
- Exports match LLD `interfaces.exports`: `LedgerAggregatesRepository`.
- Imports match LLD `depends_on`:
  - `StockLedgerModel` from `src.infrastructure.db.models.transactions`
  - `BaseRepository` from `src.infrastructure.db.repositories.base`
- `BaseRepository.__init__(session)` contract honoured — `self.session` is inherited from base (no constructor override).
- `BaseRepository[StockLedgerModel]` uses the documented `__class_getitem__` mechanism — correctly binds `self.model = StockLedgerModel` even though this repo doesn't use it (acceptable: read-only aggregator).
- Return type `list[Row]` is consumable by `DashboardService` via labelled columns (`row.inward_sum`, `row.outward_sum`, `row.adjust_sum`) as planned in T-061.

### Lens 3 — Test
- TC-123 (basic aggregation): expected output `(inward_sum=40, outward_sum=25, adjust_sum=10)` for (1,1) and `(inward_sum=15, outward_sum=0, adjust_sum=0)` for (1,2). Implementation produces these — sale row delta=-25 negated -> 25; coalesce ensures 0 for the unused source types in (1,2).
- TC-124 (empty window): empty list. Implementation returns `list(...)` of zero rows when no rows match WHERE — PASS.
- TC-125 (outward positive on two sale rows delta -15 + -25): expected outward_sum=40. Implementation: `sum(-delta)` => -(-15) + -(-25) = 40. PASS.
- TC-126 (adjust sign preserved: +5 and -12): expected adjust_sum=-7. Implementation: `case((source_type == 'adjustment', delta), else_=0)` preserves natural sign — `sum(5, -12) = -7`. PASS.

### Lens 4 — Security
- All SQL produced via SQLAlchemy Core constructs (`select`, `case`, `func.sum`, `.where`, `.between`) — fully parameterised, no string concatenation, no injection surface.
- Both parameters typed as `date` (Python type), bound positionally via SQLAlchemy parameter binding.
- No secrets, no logging, no PII handling.
- No user-controlled string fed into the query (the `'inward'/'sale'/'adjustment'` literals are hardcoded enums matching the CHECK constraint at `tbl_stock_ledger.source_type`).

### Lens 5 — Scope
- Only `backend/src/infrastructure/db/repositories/ledger_aggregates.py` created — matches `output_files[]` exactly.
- `do_not_touch[]` respected: base.py, master.py, transactions.py (repo), models/*, test files — none modified.
- No imports drag in unrelated layers; no router/service code leaked into the repository file.

## Decisions cross-check
- DS-016 (single CASE-aggregated GROUP BY): IMPLEMENTED AS DESIGNED. No tradeoff flag needed.
- DS-007 (layering): respected — file lives in `infrastructure/db/repositories/`, no upward dependencies.
- DS-003 (materialised running balance): not invoked here directly, but the design assumption holds — this repo reads delta sums from the ledger; opening/closing are handled by the service layer per LLD.

## Notes (non-issues)
- The class inherits `list/get/create/update/soft_delete` from `BaseRepository` — none are intended for use here (the StockLedger has no `is_active` column and shouldn't be CRUD'd via this repo). This is benign: the LLD scoped this repo as "read-only aggregator" and the only public method exposed in the LLD interface is `sum_deltas_by_source_type`. Callers won't accidentally invoke inherited methods because DashboardService composition only calls the documented method.
- Module docstring (lines 1-9) clearly states DS-016 anchor and index rationale — good provenance for future maintainers.

## Verdict
**CLEAN** — implementation matches plan, LLD, ADR DS-016, and all 4 referenced test cases. All 5 load-bearing properties verified. No issues across spec / contract / test / security / scope lenses.
