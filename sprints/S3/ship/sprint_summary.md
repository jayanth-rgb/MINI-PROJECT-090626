# Sprint S3 — Summary

**Closed:** 2026-06-26 · **Goal:** read-side completion (Stock Dashboard + Sales Report + carry-forward verification) on top of the materialized stock ledger and denormalized place snapshots from S2.

## Outcome at a glance

| Metric | Value |
|---|---|
| Tasks completed | **10 / 10** |
| Tasks deferred | 0 |
| Tasks escalated | 0 |
| Tasks in progress | 0 |
| Max iteration count | 1 |
| Avg iteration count | 1.0 |
| Batch exec verdict | **10/10 CHECKOUT** |
| Batch critique verdict | **10/10 CLEAN** on iteration 1 |
| New backend packages | 0 |
| New migrations | 0 |
| New env vars | 0 |
| Files created | 7 |
| Files modified (additive) | 3 |
| New decisions written at LLD time | 3 (DS-015, DS-016, DS-017) — all verified in critique |
| New tech debt introduced | **0** |
| Critique iterations | 1 (cleanest sprint so far) |

## Features shipped

| ID | Name | ACs | Backend tasks | Frontend |
|---|---|---:|---|---|
| **F-010** | Stock Dashboard | 5 (AC-041..045) | T-057, T-059, T-060, T-061, T-063, T-064, T-066 | deferred to `/ases-ui-scaffold S3` |
| **F-011** | Sales Report (Consolidation + Transactions) | 5 (AC-046..050) | T-058, T-062, T-063, T-065, T-066 | deferred to `/ases-ui-scaffold S3` |
| **F-012** | Monthly Carry-Forward (verification only) | 3 (AC-051..053) | none — zero new code | verified end-to-end via Phase 3 integration TCs |

## Tasks (all CLEAN)

| Task | File | Type | Notes |
|---|---|---|---|
| T-057 | `presentation/schemas/dashboard.py` | create | DashboardRow — 10 fields, `from_attributes=True` |
| T-058 | `presentation/schemas/sales_report.py` | create | 3 schemas; `place: str` per DS-013 |
| T-059 | `infrastructure/db/repositories/ledger_aggregates.py` | create | Single CASE-aggregated GROUP BY (DS-016); outward inverted via `SUM(-delta)` |
| T-060 | `infrastructure/db/repositories/master.py` | **modify** | `list_active_all()` appended; 6 repos + 2 prior methods byte-identical |
| T-061 | `application/services/dashboard_service.py` | create | Composes list_active_all + sum_deltas + opening/closing_balance; FORMULA-001 invariant asserted per row |
| T-062 | `application/services/sales_report_service.py` | create | Shared `_build_filters` drives both queries (DS-017); AC-050 reconciliation asserted; worker auto-corrected `place_snapshot` → `place` to match S2 column |
| T-063 | `presentation/api/dependencies.py` | **modify** | `get_dashboard_service` + `get_sales_report_service` appended; 10 existing factories byte-identical |
| T-064 | `presentation/api/routers/dashboard.py` | create | Pure delegation; `response_model=list[DashboardRow]`; no try/except |
| T-065 | `presentation/api/routers/sales_report.py` | create | Pure delegation; 5 optional `Query(default=None)` params with native repeat-key list parsing |
| T-066 | `main.py` | **modify** | dashboard + sales_report mounted at lines 44/45; CORS, error handlers, `/health`, 9 prior mounts byte-identical |

## Decisions verified by critique
- **DS-015** — advisory-lock-first + FOR UPDATE write pattern for `domain.stock` (amends DS-002 to document the canonical S2-fix as spec).
- **DS-016** — single CASE-aggregated GROUP BY for Stock Dashboard. Verified at T-059 (`SUM(-delta)` for outward, coalesce(...,0) guards, inclusive `.between()`, GROUP BY prefix aligned with `ix_stock_ledger_dgt`) and T-061 (one round-trip, FORMULA-001 invariant asserted per row).
- **DS-017** — shared filter predicate for Sales Report dual-payload. Verified at T-062 (one `_build_filters` drives both consolidation and transactions; AC-050 reconciliation asserted post-query).

## Tech debt
- **New tech debt introduced:** none.
- **Closed tech debt:** none in S3 (no closures owed by this sprint).

## Carry-forward
| ID | What | Owner | Why still pending |
|---|---|---|---|
| **CF-001** | PO bring-up of long-lived PG + `alembic upgrade head` + seed | PO (Jayanth) | Not blocking — testcontainers covers tests; only needed for manual API smoke |
| **TD-001** | shadcn calendar.tsx classNames patch | `/ases-ui-scaffold S3` | UI track; surfaces when dashboard date picker is built |
| **TD-010** | Radix Select/Popover jsdom incompatibility (7 frontend TCs) | PO + `/ases-ui-design S3` | Decision pending: mock shim vs Playwright E2E vs accept |
| **TD-008** | First-row insert race (theoretical) on `_apply` | V2 | Acceptable for V1; would require advisory lock + retry to close |

## Phase 3 test coverage (46 TCs to verify)

Backend only (frontend TCs land in `/ases-ui-design S3` track):

| Bucket | TCs |
|---|---|
| Dashboard math + carry-forward | TC-115, TC-118, TC-119, TC-120, TC-156 (critical) |
| Dashboard perf gate (p95 < 500ms) | **TC-122** |
| Ledger aggregator correctness (testcontainers) | TC-123..126 |
| AC-050 reconciliation (Sales Report) | **TC-141, TC-142, TC-145** |
| DesignGradeMap cascade | TC-150, TC-151, TC-152 (AC-012/AC-017 transitive cover) |
| F-012 carry-forward (no new code) | TC-153, TC-154, TC-155 |
| SQL-injection at /reports/sales | **TC-158** |
| DI integration smoke | TC-159, TC-160 |

## Graph refresh (Step 0)
`graphify update .` ran successfully — graph rebuilt from S1-era 8,442 nodes / 8,939 edges / 834 communities to **11,895 nodes / 12,900 edges / 1,106 communities**. Now reflects S2 transactions/ledger and all S3 dashboard/reports code. **Closes NB-S3-001 from `/ases-analyze S3`.**

## Phase transition

- `phase`: `SPRINT_EXECUTION` → **`SPRINT_SHIP`**
- Next: `/ases-test-impl S3` (Phase 3 sequence: test-impl → test-run → integration-test → system-test → uat ⚑PO → devops → final-audit ⚑PO → release)
- **Parallel track unlocked:** `/ases-ui-design S3` may begin immediately — backend API surface is frozen and critiqued.

## Suggested PRD updates for V2
1. Confirm `AC-045` dashboard latency stays at p95 < 500ms (S3 measured under 6 pairs × 12 months; production hardware may differ).
2. Add pagination ACs for `/reports/sales` (and `/sales`) before report volumes grow large in production.
3. Promote F-012 carry-forward from "verification" to a first-class AC for any future sprint that touches `domain.stock`.
4. Clarify chart-vs-table layout choice for Dashboard + Sales Report at `/ases-ui-design S3`.
