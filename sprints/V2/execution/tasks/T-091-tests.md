# T-091 tests — routers/invoices.py (TC-217)

Integration test using FastAPI TestClient + testcontainers PostgreSQL.

| TC | Endpoint | Setup | Expected |
|---|---|---|---|
| TC-217 | POST /invoices?sales_header_id=\<id\> | SUPERVISOR auth; seed: dealer, sales_header, 2 sales_lines (qty=10 @ 100.00, qty=5 @ 80.00), price master records | 201; invoice_number starts with 'INV-'; total_amount=1400.00; status='PENDING'; lines_count=2; each line.unit_price snapshotted (DS-022) |

**Note on sales_header_id**: Passed as query param, not body (`POST /invoices?sales_header_id=1`). Test client call: `client.post("/invoices", params={"sales_header_id": header_id}, headers=auth_headers)`.

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc217_invoices_router_create.py`

See [test_cases.json](../../design/test_cases.json) TC-217 for full inputs/expected_output.
