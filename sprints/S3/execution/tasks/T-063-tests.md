# T-063 tests — 2 integration TCs

| TC | Type/Priority | Asserts |
|----|---|---|
| TC-159 | integration/high | GET /api/v1/dashboard?as_of_date=2026-06-30 resolves through `get_dashboard_service` and returns 200 with a valid response. |
| TC-160 | integration/high | GET /api/v1/reports/sales (no filters) resolves through `get_sales_report_service` and returns 200 with `consolidation + transactions` payload. |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> Both tests live in the router integration files (`backend/tests/integration/api/test_dashboard_api.py` and `test_sales_report_api.py`) — DI is verified transitively via the FastAPI test client at `/ases-test-impl S3` time.
