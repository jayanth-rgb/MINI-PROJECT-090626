# T-078 tests — routers/inward_report.py (TC-214)

Integration test using FastAPI TestClient + testcontainers PostgreSQL.

| TC | Endpoint | Setup | Expected |
|---|---|---|---|
| TC-214 | GET /reports/inward?date_from=2025-01-01&supplier_ids=\<id\> | Seed: supplier, design, grade, 2 inward ledger records (same design+grade, different dates); SUPERVISOR auth | 200; consolidation list non-empty; transactions list non-empty; sum(transactions[*].nos) == sum(consolidation[*].total_nos) |

**DS-017 invariant check**: The reconciliation assertion (sum of transaction nos == sum of consolidation total_nos) is verified both by the service (InwardReportService raises if violated) and by this test.

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc214_inward_report_router.py`

See [test_cases.json](../../design/test_cases.json) TC-214 for full inputs/expected_output.
