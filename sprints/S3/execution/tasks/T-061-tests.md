# T-061 tests — 11 TCs (covers all F-010 ACs + F-012 carry-forward)

| TC | Type/Priority | AC | Asserts |
|----|---|---|---|
| TC-115 | integration/critical | AC-041 | 3 active pairs + mixed ledger movements → 3 DashboardRow with all 10 fields populated. |
| TC-116 | edge/critical | AC-041 | Zero active pairs → empty list (valid outcome, not an error). |
| TC-118 | integration/critical | AC-042 | Opening column = closing of last day of previous month (DS-004). |
| TC-119 | integration/critical | AC-043 | Inward + outward + adjust columns derived from monthly aggregates. |
| TC-120 | integration/critical | AC-044 | Closing column = latest running_balance ≤ as_of_date (DS-003). |
| TC-121 | edge/critical | AC-044 | (design, grade) with NO movements in window → opening = closing, all three movement columns = 0. |
| **TC-122** | **performance/critical** | **AC-045** | **p95 < 500ms over 10 runs with 6 active pairs × 12 months of ledger data.** |
| TC-127 | unit/high | AC-043 | Movement aggregation: pairs without ledger entries default to {inward:0, outward:0, adjust:0}. |
| TC-128 | edge/high | AC-044 | Invariant assertion: opening + inward − outward + adjust == closing per row (AssertionError raised if not). |
| TC-129 | unit/high | AC-041 | Result sorted by (design_name ASC, grade_code ASC). |
| **TC-156** | **integration/critical** | **AC-053** | **F-012 carry-forward: back-dated sale crossing a month boundary → recompute_forward updates running_balance → dashboard for the LATER month reflects the corrected opening.** |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> Tests live in `backend/tests/integration/api/test_dashboard_api.py` (where the FastAPI client + testcontainers PG are wired) and `backend/tests/unit/application/services/test_dashboard_service.py` (for the pure unit-shaped TC-127/128/129) at `/ases-test-impl S3` time.
