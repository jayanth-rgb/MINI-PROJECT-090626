# T-088 tests — routers/report_export.py (TC-215..TC-216)

Integration tests using FastAPI TestClient + testcontainers PostgreSQL.

| TC | Endpoint | Setup | Expected |
|---|---|---|---|
| TC-215 | GET /reports/sales/export?format=pdf | SUPERVISOR auth; seeded dealer + sales data | 200; Content-Type=application/pdf; Content-Disposition contains 'attachment'; response body first 4 bytes == b'%PDF' |
| TC-216 | GET /reports/inward/export?format=xlsx | SUPERVISOR auth; seeded supplier + inward data | 200; Content-Type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; body first 4 bytes == b'PK\x03\x04' (ZIP/xlsx magic) |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc215_report_export_router_sales_pdf.py`

See [test_cases.json](../../design/test_cases.json) TC-215..TC-216 for full inputs/expected_output.
