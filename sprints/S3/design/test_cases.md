# Sprint S3 — Test Cases

**Produced:** 2026-06-26 · **Tester:** Opus
**Scope:** F-010 Stock Dashboard + F-011 Sales Report + F-012 Carry-Forward (13 ACs)

## Summary

| Metric | Value |
|---|---|
| Total test cases | **46** (TC-115 .. TC-160) |
| ACs covered | **13 / 13** (100%) |
| Frameworks | pytest × 46 (frontend TBD at `/ases-ui-design S3`) |
| Critical priority | 35 |
| High priority | 11 |

## Test type distribution

| Type | Count | Notes |
|---|---|---|
| unit | 8 | Repository methods, service argument forwarding, ordering |
| integration | 27 | End-to-end via real testcontainer PostgreSQL |
| edge | 8 | Empty inputs, invariant violations, soft-delete semantics |
| performance | 2 | AC-045 dashboard p95 < 500ms; PRD Sales Report < 2s |
| security | 1 | SQL injection via filter params (FastAPI + SQLAlchemy parameter binding) |

## AC coverage map

### F-010 Stock Dashboard

| AC | Description | Test cases |
|---|---|---|
| AC-041 | One row per active design×grade with 5 stock columns | TC-115, TC-116, TC-117, TC-123, TC-124, TC-125, TC-126, TC-129, TC-130, TC-131, TC-132, TC-150, TC-159 |
| AC-042 | First-month opening = 0 (FORMULA-002 base case) | TC-118 |
| AC-043 | Month-rollover: Opening of day-1 = Closing of prev-month last day | TC-119, TC-127 |
| AC-044 | Closing = Opening + Inward − Outward + Adjust (FORMULA-001) | TC-120, TC-121, TC-128 |
| AC-045 | Sub-second performance with 12 months of data | TC-122 |

### F-011 Sales Report

| AC | Description | Test cases |
|---|---|---|
| AC-046 | All filters optional + multi-select; no filters = full dataset | TC-133, TC-134, TC-135, TC-136, TC-143, TC-144, TC-147, TC-148, TC-149, TC-157, TC-158, TC-160 |
| AC-047 | Consolidation GROUP BY (design, grade) SUM(nos) | TC-137, TC-138, TC-146 |
| AC-048 | Transaction per-line ORDER BY sales_date ASC | TC-139 |
| AC-049 | Both sections render in single response payload | TC-140 |
| AC-050 | sum(transactions.nos) ≡ sum(consolidation.total_nos) | TC-141, TC-142, TC-145 |

### F-012 Carry-Forward

| AC | Description | Test cases |
|---|---|---|
| AC-051 | First Month-N+1 txn opening = Month-N last day closing | TC-153 |
| AC-052 | No prior month data → opening = 0 | TC-154 |
| AC-053 | Back-dated cross-month transaction keeps carry-forward correct | TC-155, TC-156 |

### Regression coverage from S1 (incidentally re-verified)

| AC | Test cases |
|---|---|
| AC-012 (Grade soft-delete cascade) | TC-152 |
| AC-017 (DesignGradeMap soft-delete) | TC-151 |

## LLD interface coverage

All 6 files with `test_required: true` have ≥1 unit + ≥1 integration test:

| LLD file | Unit tests | Integration tests |
|---|---|---|
| `ledger_aggregates.py` | TC-123, TC-124, TC-125, TC-126 | (used transitively by TC-115, TC-117) |
| `dashboard_service.py` | TC-115, TC-116, TC-127, TC-128, TC-129 | TC-118, TC-119, TC-120, TC-121, TC-122, TC-156 |
| `dashboard.py` (router) | — | TC-117, TC-130, TC-131, TC-132, TC-159 |
| `sales_report_service.py` | TC-143, TC-144, TC-145, TC-146 | TC-133, TC-134, TC-135, TC-136, TC-137, TC-138, TC-139, TC-141, TC-142, TC-157 |
| `sales_report.py` (router) | — | TC-140, TC-147, TC-148, TC-149, TC-158, TC-160 |
| `master.py` (MODIFY) | TC-150, TC-151, TC-152 | (used transitively by TC-117) |

Files with `test_required: false` (Pydantic schemas, DI factories, main.py wiring) are correctly excluded from direct tests but are smoke-covered indirectly via router tests.

## HLD data-flow coverage

| Data flow | Test cases |
|---|---|
| DF-004 (Dashboard → GET /dashboard) | TC-117, TC-130, TC-159 |
| DF-005 (Sales Report → GET /reports/sales) | TC-140, TC-147, TC-148, TC-160 |

## Key invariants tested

1. **FORMULA-001** (`opening + inward − outward + adjust = closing`) — TC-120, TC-121, TC-128 (defensive assertion)
2. **FORMULA-002** (`opening_balance(m_first) = closing_balance(m_first − 1 day)`) — TC-119, TC-153, TC-155
3. **AC-050** (`Σtransactions.nos == Σconsolidation.total_nos` under DS-017 shared filter) — TC-141, TC-142, TC-145

## Edge cases explicitly enumerated

| Edge case | Test |
|---|---|
| Zero active pairs → empty response, not 404 | TC-116 |
| Empty date window → empty aggregate | TC-124 |
| Sale rows (negative delta) → outward reads positive | TC-125 |
| Negative adjustment (shrinkage) → adjust_sum negative | TC-126 |
| Ledger row past as_of_date → excluded from sums | TC-121 |
| Tampered running_balance → invariant assertion catches it | TC-128 |
| `dealer_ids=[]` (empty list) → treated as no filter | TC-144 |
| AC-050 invariant violation → AssertionError | TC-145 |
| Soft-deleted map row excluded | TC-151 |
| Soft-deleted grade transitively excluded | TC-152 |
| Back-dated cross-month txn → recompute forward correct | TC-155, TC-156 |

## Performance thresholds

| TC | Scenario | Threshold | Source |
|---|---|---|---|
| TC-122 | Dashboard with ~4320 ledger rows | p95 < 500ms | AC-045 + PRD non_functional.performance |
| TC-157 | Sales Report unfiltered, 1 year of data | p95 < 2000ms | PRD non_functional.performance |

## Security tests

| TC | Vector | Defense |
|---|---|---|
| TC-149 | Malformed date_from query string | FastAPI 422 (Pydantic date parser) |
| TC-158 | SQL-injection via `places` filter | SQLAlchemy parameter binding → returns 0 rows, no 500 |

## Frontend tests deferred

S3's UI track (dashboard page + sales report dual-pane) goes through `/ases-ui-design S3` → `/ases-ui-review S3` → `/ases-ui-scaffold S3` → `/ases-test-impl S3`. The 4 typical jest cases (date-picker UX, multi-select filter chip behavior, dual-pane render, table sort) will be appended after the UI scaffold lands.

## Next

→ `/ases-sprint-gate S3`
