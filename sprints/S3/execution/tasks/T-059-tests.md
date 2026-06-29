# T-059 tests — 4 TCs (1 critical unit + 3 edge)

| TC | Type/Priority | Asserts |
|----|---|---|
| TC-123 | unit/critical | Basic aggregation: 1 design × 2 grades with mixed inward+sale rows in window → exactly 2 result rows with correct CASE-aggregated SUMs (outward reads positive). |
| TC-124 | edge/high | Empty window (no ledger rows between month_start and as_of_date) → empty list returned. |
| TC-125 | edge/critical | Window edges INCLUSIVE: rows on exactly month_start and exactly as_of_date are included; rows one day outside are excluded. |
| TC-126 | edge/critical | All three source types (inward+sale+adjustment) for one (design, grade) in the same window → single row with each SUM column correctly attributed. |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> ⚠ Tests are testcontainers-backed integration tests on the file system (per S1/S2 precedent that repository "unit" tests in this project hit real PG via `pg_container` fixture). They live in `backend/tests/integration/db/test_ledger_aggregates.py` at `/ases-test-impl S3` time.
