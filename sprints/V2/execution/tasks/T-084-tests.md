# T-084 tests — services/invoice_service.py (TC-202..TC-206)

Integration tests requiring PostgreSQL (testcontainers).

| TC | Method | Setup | Expected |
|---|---|---|---|
| TC-202 | `create_from_sales(1)` | 2 sales lines (10×100.00, 5×80.00) + prices | total_amount=1400.00; status=PENDING; lines_count=2; invoice_number starts 'INV-'; line unit_prices snapshotted |
| TC-203 | `create_from_sales(1)` | Existing invoice for sales_header_id=1 | HTTPException 409 |
| TC-204 | `get_invoice(id)` after price edit | Invoice created; price master unit_price changed to 200.00 | invoice_line.unit_price unchanged at 100.00 |
| TC-205 | `record_payment(id, amount=500.00)` | Invoice total=500.00, PENDING | status=PAID; payments_count=1 |
| TC-206 | `record_payment(id, amount=200.00)` | Invoice total=500.00; existing payment=400.00 | HTTPException 422 |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc202_invoice_service_create_from_sales.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-202..TC-206 for full inputs/expected_output.
