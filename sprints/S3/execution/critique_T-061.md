# Critique — T-061 · `application/services/dashboard_service.py`

**Sprint:** S3 · **Module:** M-004 · **Critic:** Opus 4.7 · **Date:** 2026-06-26

## Verdict

**CLEAN** — 0 critical, 0 major, 0 minor.

DashboardService.list_as_of is a textbook M-004 orchestrator. Single round-trip for the aggregate, O(1) per-pair opening/closing via existing S2 domain primitives, FORMULA-001 asserted per row, Python-side sort by (design_name, grade_code), zero SQL composition in the service. All 7 load-bearing properties verified against source. Honours DS-003, DS-004, DS-016; respects all `do_not_touch` boundaries.

## Decisions consulted

| ID | Relevance |
|---|---|
| DS-002 | Advisory-lock-first writes — write-path concern; this is a read-only service. Not a constraint on this file. |
| DS-003 | running_balance materialised → opening/closing are O(1). Service calls the domain primitives that exploit this. |
| DS-004 | opening = closing(prev-day). Encapsulated in `domain.stock.opening_balance`; service does NOT re-derive. |
| DS-015 | p95 < 500ms perf target. Architecture (1 + 1 + 2N indexed lookups) preserves the budget. |
| DS-016 | SINGLE GROUP BY for dashboard. Service makes exactly one call to `sum_deltas_by_source_type`. |

## Load-bearing property matrix

| # | Property | Status | Evidence |
|---|---|---|---|
| 1 | Single round-trip for the aggregate | PASS | Line 57: one call to `sum_deltas_by_source_type`, outside the per-pair loop. |
| 2 | O(1) per-pair opening/closing via domain primitives | PASS | Lines 74-75: direct calls to `opening_balance` / `closing_balance` from `src.domain.stock`. No re-implementation. |
| 3 | FORMULA-001 invariant asserted | PASS | Lines 79-83: `assert opening + inward - outward + adjust == closing` with diagnostic message. |
| 4 | Sort by (design_name ASC, grade_code ASC) | PASS | Line 104: `rows.sort(key=lambda r: (r.design_name, r.grade_code))`. Not by id. |
| 5 | No direct SQL in service | PASS | No `text`, `select`, `func`, `case`, or `execute` imports. Pure orchestration. |
| 6 | `month_first = as_of_date.replace(day=1)` | PASS | Line 50, used both as aggregate `month_start` and as input to `opening_balance` (which subtracts 1 day per DS-004). |
| 7 | Eager-loaded `pair.design`/`pair.grade` | PASS | `DesignGradeMapModel` declares both relationships with `lazy='joined'` (master.py:101-102). Service reads `.design.design_name`, `.design.size`, `.grade.grade_code` without follow-up queries. |

## Five-lens results

### Lens 1 — Spec
PASS. Signature matches LLD `files[2]`: `class DashboardService` with `__init__(session: Session)` and `list_as_of(as_of_date: date) -> list[DashboardRow]`. All 5 LLD-prescribed steps (month_first, list_active_all, single GROUP BY, per-pair lookups + default-0 missing-pair handling, invariant assert) appear in order, followed by the LLD-pinned sort. `plan.json::output_files[]` matches the single file produced.

### Lens 2 — Contract
PASS. Exports `DashboardService` (matches LLD `interfaces.exports`). All imports from `depends_on[]` are present and used:
- `src.domain.stock` — `opening_balance`, `closing_balance` (signatures verified: `(session, design_id, grade_id, date) -> int`).
- `src.infrastructure.db.repositories.ledger_aggregates.LedgerAggregatesRepository` — `sum_deltas_by_source_type(month_start, as_of_date)` returns `list[Row]` with `.design_id/.grade_id/.inward_sum/.outward_sum/.adjust_sum` (verified against ledger_aggregates.py:23-79).
- `src.infrastructure.db.repositories.master.DesignGradeMapRepository` — `list_active_all()` returns `list[DesignGradeMapModel]` (verified against master.py:59-70).
- `src.presentation.schemas.dashboard.DashboardRow` — constructed with all 10 declared fields.

### Lens 3 — Test
PASS. Each of the 11 referenced test cases is satisfied by the implementation:

| TC | Coverage |
|---|---|
| TC-115 | 3 pairs × all 10 fields populated → constructed from `pair.design/.grade` + `mov` + `opening` + `closing`. |
| TC-116 | Zero active pairs → `list_active_all` returns `[]`, loop is no-op, `rows = []` returned. |
| TC-118 | Opening = closing(prev-day) → delegated to `opening_balance` per DS-004. |
| TC-119 | Movement columns from monthly aggregate → built from `sum_deltas_by_source_type` Row tuples. |
| TC-120 | Closing = latest `running_balance` ≤ `as_of_date` → delegated to `closing_balance` per DS-003. |
| TC-121 | No movements in window → `agg_by_key.get(key, {inward:0, outward:0, adjust:0})` defaults; invariant holds because no movement implies `opening == closing`. |
| TC-122 | p95 < 500ms → architecture (1 + 1 + 2N indexed lookups) fits the budget for 6 pairs. |
| TC-127 | Default 0 for pairs without ledger entries → explicit default dict in `.get` fallback. |
| TC-128 | AssertionError on invariant break → bare `assert` (not `if … raise …`) with diagnostic message. |
| TC-129 | Sort by (design_name, grade_code) → explicit `rows.sort(...)`. |
| TC-156 | Back-dated cross-month carry-forward → `opening_balance` reads the live materialised `running_balance` which has been re-rolled by `_recompute_forward` at write time (S2 contract); service needs no extra code. |

### Lens 4 — Security
PASS. No SQL composition in this file, no user-controlled strings reach a query string, no secrets or PII. `as_of_date.replace(day=1)` is a `date` method, not a string operation. Assertion error message contains only int IDs and int balances. `assert` is used as the documented hard invariant per DS-016 + FORMULA-001 — not as a defensive check; even under `python -O` the worst case is silent passthrough of corrupt data, which is a separate (write-path-prevented) bug class. No auth concerns per DS-005 (V1 has no auth).

### Lens 5 — Structural / Scope-creep
PASS. File contains exactly one class with one public method plus `__init__`. No additional exports, no helper functions outside the class, no modifications to any `do_not_touch` file (verified: `domain/stock.py`, repositories, `schemas/dashboard.py` untouched). No router code, no DI factory (correctly deferred to T-062/T-063). The service is the minimum surface area to satisfy the plan. Direct imports all resolve against existing modules; the orchestration call graph from `list_as_of` → `list_active_all` + `sum_deltas_by_source_type` + `opening_balance` + `closing_balance` + `DashboardRow.__init__` is explicit. Service will be reachable from `GET /api/v1/dashboard` once T-062 wires the router.

## Issues

None.

## Recommendation

Proceed to T-062 (router) and T-063 (DI factory). Subsequent integration test impl (`/ases-test-impl S3`) can rely on this orchestrator without reservation.
