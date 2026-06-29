# T-064 tests — 4 TCs (2 integration + 1 edge + 1 security)

| TC | Type/Priority | Asserts |
|----|---|---|
| TC-117 | integration/critical | GET /api/v1/dashboard?as_of_date=2026-06-30 → 200 with seeded rows; JSON body is a list of objects with all 10 DashboardRow keys. |
| TC-130 | integration/critical | response_model serialization: rows are sorted (design_name ASC, grade_code ASC) in the HTTP response. |
| TC-131 | edge/high | GET /api/v1/dashboard with NO as_of_date → 422 (FastAPI's required-Query default behavior). |
| TC-132 | security/high | GET /api/v1/dashboard?as_of_date=not-a-date → 422 (FastAPI rejects at parse time; service never invoked). |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> All 4 tests live in `backend/tests/integration/api/test_dashboard_api.py` at `/ases-test-impl S3`. They exercise the full stack (FastAPI client + DI + service + repo + testcontainers PG) so they double as smoke tests for T-063 + T-066.
