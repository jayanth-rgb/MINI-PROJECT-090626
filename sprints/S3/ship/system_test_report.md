# Sprint S3 — System Test Report

**Executed:** 2026-06-29 · **Re-run:** 2026-07-01 · **Verdict:** **PASS** (5/5, 31 tests)

| ID | Type | Threshold | Actual | Result |
|---|---|---|---|:-:|
| **ST-008** | performance | Dashboard p95 < 800ms (PRD "sub-second") | **p95 = 33.1ms · p50 = 24.8ms** | ✅ ~24x headroom |
| **ST-009** | performance | Sales Report p95 < 2000ms (PRD "< 2s for 1 yr") | **p95 = 715.7ms · p50 = 363.2ms** | ✅ ~2.8x headroom |
| **ST-010** | security | 3 SQL-injection payloads neutralized + tbl_sales_header intact | 3/3 neutralized; seed row intact | ✅ |
| **ST-011** | security | V1 no-auth posture for 2 new S3 endpoints | 4/4 GETs return 200 | ✅ |
| **ST-012** | boundary | Soft-delete cascade: dashboard hides pair, sales report retains history | 3/3 phases verified | ✅ |

**Fix iterations needed: 0.** All scenarios passed first execution.

## NFR coverage

| PRD NFR | Scenarios | Verdict |
|---|---|---|
| Performance — "sub-second dashboard; < 2s sales report" | ST-008, ST-009 | **PASS** with substantial headroom |
| Security — "all inputs validated server-side; V1 no auth" | ST-010, ST-011 | **PASS** |
| Scalability — "single-digit concurrent users" | covered by S2 ST-007 (DS-002/DS-015) — S3 is read-only | N/A new surface |
| Accessibility — "keyboard-navigable forms" | owned by `/ases-ui-scaffold S3` | N/A backend sprint |

## Risk coverage

| HLD risk | Severity | S3 verification |
|---|---|---|
| R-001 (concurrent ledger races) | critical | covered by S2 ST-007 (no new write surface in S3) |
| R-002 (dashboard SUM scales) | medium | **ST-008** — DS-003 materialized ledger + DS-016 single GROUP BY operate well within sub-second budget |
| R-003 (back-date recompute) | medium | covered by S2 ST-007 + S3 IS-008/IS-012 |
| R-004 (no auth in V1) | medium | **ST-011** — confirmed for 2 new S3 endpoints |
| R-005 (soft-delete with history) | low | **ST-012** — dashboard hides deactivated pair; sales report retains historical sales via FK |

## Scenario details

### ST-008 — Dashboard HTTP latency
Seeded 6 active pairs × 12 months × 28 txns/month (= 2016 ledger rows) using per-pair cumulative `running_balance` so FORMULA-001 holds at every read. 3 warmups + 30 timed `TestClient.get("/api/v1/dashboard?as_of_date=<today>")` calls. **p95 = 33.1ms** vs 800ms threshold. The ~24x headroom is partly testcontainers-local network (zero latency) — production network adds ~50-150ms but stays comfortably under the PRD "sub-second" bar.

### ST-009 — Sales Report HTTP latency
Seeded 6 dealers × 12 months × 50 sales/month × 3 lines/sale → 3,600 headers + **10,800 sales_line rows**. 2 warmups + 15 timed unfiltered `GET /api/v1/reports/sales` calls. **p95 = 715.7ms** vs 2000ms PRD threshold. The dual-payload (consolidation + transactions) shared-predicate plan from DS-017 + `ix_sales_header_sales_date` + `ix_sales_line_dgd` indexes keep both queries under budget.

### ST-010 — SQL-injection across all 3 list-type filters
Extends TC-158 (which only covered `places`). All 3 payloads handled correctly:
- `dealer_ids="1; DROP TABLE tbl_sales_header;--"` → **422** (FastAPI parse rejection — never reaches the service)
- `design_ids="(SELECT design_id FROM tbl_trading_design)"` → **422** (same)
- `places="'; DROP TABLE tbl_sales_header;--"` → **200**, `consolidation=[]`, `transactions=[]` (SQLAlchemy `.in_()` parameter binding — literal string matched no row)

Post-loop assertion: `tbl_sales_header` still contained the seed row, confirming none of the DROP attempts executed.

### ST-011 — V1 no-auth posture for 2 new S3 endpoints
4 assertions, all 200:
- `GET /api/v1/dashboard?as_of_date=<today>` — no Authorization header
- Same — with `Authorization: Bearer fake`
- `GET /api/v1/reports/sales` — no Authorization header
- Same — with `Authorization: Bearer fake`

FastAPI ignores unconfigured auth schemes, so a bogus Bearer header doesn't change behavior. This test locks in the V1 contract — when V2 adds auth, this test will start failing, signaling the intentional contract change.

### ST-012 — Soft-delete post-history boundary
Three-phase end-to-end test of R-005 mitigation:
- **(a) Active pair**: seed inward=+100, sale=-20 for "16X10 Ridges + grade '2'"; GET /dashboard → row with `closing=80`.
- **(b) Deactivate**: `map.is_active=False` + flush; GET /dashboard → pair is **gone** from response (DesignGradeMapRepository.list_active_all correctly filters via JOIN on `grade.is_active AND map.is_active`).
- **(c) Historical fidelity**: seed historical SalesHeader + SalesLine for the deactivated pair; GET /reports/sales → the sale appears in BOTH `transactions[]` (nos=20) AND `consolidation[]` (total_nos=20). FK join into `tbl_design_grade_map` is unaffected by `is_active`, so historical reports preserve their integrity even after a mapping is soft-deleted.

## Production code observations
**None.** No failures, no fix iterations, no production source changes required.

## Framework note
Performance scenarios use `time.perf_counter()` + `statistics.quantiles` (S2 ST-004 idiom) instead of `pytest-benchmark` because the latter isn't installed in the project venv. Adding a backend test dep mid-Phase-3 needs PO approval — and the perf_counter idiom is already established in S2.

## Re-run (2026-07-01)

`pytest tests/system/ -v` collected 31 tests across 17 files — **31 passed, 0 failed** in 51.3s. All 5 S3 scenarios (ST-008..ST-012) remain green. No regressions. 1 pre-existing `asyncio_default_fixture_loop_scope` deprecation warning, non-blocking.

## Next
**Gate PASS** → **`/ases-uat S3`** (PO reviews UAT checklist against PRD acceptance criteria).
