# Sprint S3 — Release

**Released:** 2026-06-29 16:00 +05:30 · **Verdict:** **SHIPPED** ✅ · **V1 Status:** 🎉 **FEATURE COMPLETE**

## Goal
Reporting & Carry-Forward — Stock Dashboard (date-filtered), Sales Report (Consolidation + Transaction dual-pane with multi-select filters), explicit verification of monthly carry-forward including back-dated transactions across month boundaries.

## What shipped

| Feature | Backend ACs | UI ACs | Endpoint | UI |
|---|---:|---:|---|---|
| **F-010** Stock Dashboard | 5 / 5 | 1 / 1 | `GET /api/v1/dashboard?as_of_date=YYYY-MM-DD` | DashboardPage — shipped 2026-07-01 |
| **F-011** Sales Report | 5 / 5 | 4 / 4 | `GET /api/v1/reports/sales` (5 multi-select filters) | SalesReportPage — shipped 2026-07-01 |
| **F-012** Monthly Carry-Forward | 3 / 3 | n/a | verified via existing S2 domain.stock — no new code | n/a |

## Commits
- **Backend:** `d9715d5eeabebfa63f8f142b659bf1800b95a36c` on `develop` · 131 files (+11,594 / -10) · co-authored by Claude Opus 4.7
- **UI track (supplemental):** `56bd4b7` on `develop` · DashboardPage + SalesReportPage wired; 10 jest TCs added; TD-010 closed

## New architectural decisions

| ID | What |
|---|---|
| **DS-015** | Advisory-lock-first stock-ledger writes (amends DS-002 to canonize the TD-011 fix from S2) |
| **DS-016** | Single CASE-aggregated GROUP BY for Stock Dashboard |
| **DS-017** | Shared filter predicate for Sales Report dual payload — makes AC-050 reconciliation structurally impossible to violate |

## Test totals at ship

| Suite | Count | Result |
|---|---:|---|
| Unit + integration pytest | 158 | **158 PASS** |
| Frontend jest (TC-161..TC-170) | 10 | **10 PASS** |
| Integration scenarios (IS-005..IS-012) | 8 | **8 PASS** |
| System test scenarios (ST-001..ST-012) | 12 | **12 PASS** |
| **Total (pytest + jest)** | **168** | **168 PASS · 0 regressions** |

## Perf at ship

| Metric | p50 | **p95** | Threshold | Headroom |
|---|---:|---:|---:|---|
| Dashboard (HTTP) | 24.8 ms | **33.1 ms** | 800 ms | ~24× |
| Sales Report (HTTP, 10,800 lines) | 363.2 ms | **715.7 ms** | 2000 ms | ~2.8× |

## Tech debt

- **New tech debt introduced by S3: 0**
- **Closed in S3: 1** — TD-010 (Radix UI jsdom incompatibility → MultiSelectComboboxFallback)
- **Carry-forwards** (none blocking release):

| ID | Severity | Target | Note |
|---|---|---|---|
| CF-001 | minor | PO action (post-release optional) | Long-lived PG bring-up; testcontainers covered all 168 tests |
| TD-001 | minor | UI-track (next sprint) | shadcn calendar.tsx patch (Dashboard date-picker) |
| **TD-010** | minor | **CLOSED 2026-07-01** | MultiSelectComboboxFallback — TC-169 + TC-170 PASS |
| TD-008 | minor | V2 | First-row insert race (theoretical) |

## Phase 3 fix iterations
**2 iterations, 100% test-side.** Production source was not modified during Phase 3. Every failure was caught by production-level invariants (AC-021 7-day window, FORMULA-001 ledger invariant, AC-050 reconciliation) — defense-in-depth working exactly as designed.

## V1 Completion 🎉

| | |
|---|---|
| Features shipped | **12 / 12** (F-001..F-012) |
| Modules shipped | M-001 master · M-002 API · M-003 ledger · M-004 dashboard · M-005 reports · M-007 persistence (M-006 UI deferred to UI tracks) |
| Sprints in V1 | S1 (data foundation) → S2 (transaction forms + ledger) → S3 (reporting + carry-forward) |
| First commit | `571c601` (2026-06-20, S1 ship) |
| Last commit | `56bd4b7` (2026-07-01, S3 UI track supplemental) |
| Total tests | **168 / 168** PASS across V1 (158 pytest + 10 jest) |
| Open carry-forwards into V2 | 3 (CF-001 operational, TD-001 UI-track, TD-008 V2 theoretical) |

## UI Track Supplemental — 2026-07-01

| Item | Result |
|---|---|
| DashboardPage wired to `GET /api/v1/dashboard` | **SHIPPED** |
| SalesReportPage: ConsolidationTable + TransactionTable simultaneous render | **SHIPPED** |
| AC-049-UI visual verification (no toggle, no tab, Consolidation first) | **RESOLVED** |
| TD-010 closed (MultiSelectComboboxFallback) | **CLOSED** |
| Jest TCs TC-161..TC-170 | **10/10 PASS** |
| PO approval of final audit | **APPROVED · Jayanth · 2026-07-01** |

## Next sprint

**`/ases-prd-update V2`** or **`/ases-lld V2`** — V2 design phase. Scope drawn from `contracts/roadmap.json` `deferred[]`: auth/RBAC, pricing/invoicing, Inward Report, PDF/Excel exports, manufacturing tiles.

## Phase transition
`SPRINT_SHIP` → **`SPRINT_DESIGN`** (next sprint). `context.json` `current_sprint` set to "S3 (closed)" pending PO's choice of next-sprint id.

## Signed
- PO: Jayanth · SHIP APPROVED 2026-07-01 (UI track supplemental — final verdict)
- /ases-release: 2026-06-29 16:00 +05:30 (initial) · 2026-07-01 (supplemental — UI track complete)
