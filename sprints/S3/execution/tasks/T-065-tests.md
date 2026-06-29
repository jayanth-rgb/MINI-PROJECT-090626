# T-065 tests — 5 TCs (3 integration + 2 security)

| TC | Type/Priority | Asserts |
|----|---|---|
| TC-140 | integration/critical | GET /api/v1/reports/sales (no filters) → 200 with `{consolidation: [...], transactions: [...]}`. |
| TC-147 | integration/critical | Multi-select repeat-key parsing: `?dealer_ids=1&dealer_ids=2&places=Mysuru&places=Bengaluru` → service receives `dealer_ids=[1,2]` and `places=["Mysuru","Bengaluru"]`. |
| TC-148 | integration/critical | All 5 filters set simultaneously → 200 with filtered payload satisfying AC-050 (reconciles). |
| TC-149 | security/high | GET with `?dealer_ids=foo` → 422 (FastAPI rejects non-int at parse time). |
| **TC-158** | **security/critical** | **GET with `?places=' OR 1=1 --` → safely parameterized: query returns rows matching the literal string "' OR 1=1 --" in `place_snapshot`, NOT all rows. Verifies SQLAlchemy `.in_()` parameter binding (no string interpolation in T-062's `_build_filters`).** |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> All 5 tests live in `backend/tests/integration/api/test_sales_report_api.py` at `/ases-test-impl S3`. TC-158 is the load-bearing security test for the F-011 endpoint.
