# T-081 tests — domain/invoice.py (TC-176..TC-184)

All unit tests. No DB required.

| TC | Function | Input | Expected |
|---|---|---|---|
| TC-176 | `compute_line_total` | qty=10, price='150.00' | Decimal('1500.00') |
| TC-177 | `compute_line_total` | qty=0, price='150.00' | raises ValueError |
| TC-178 | `compute_line_total` | qty=5, price='-10.00' | raises ValueError |
| TC-179 | `compute_invoice_total` | [100.00, 200.50, 50.25] | Decimal('350.75') |
| TC-180 | `compute_invoice_total` | [] | raises ValueError |
| TC-181 | `compute_invoice_status` | total=1000.00, paid=[] | 'PENDING' |
| TC-182 | `compute_invoice_status` | total=1000.00, paid=[400.00] | 'PARTIAL' |
| TC-183 | `compute_invoice_status` | total=1000.00, paid=[600.00, 400.00] | 'PAID' |
| TC-184 | `generate_invoice_number` | date(2026,7,2), id=42 | 'INV-20260702-00042' |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/unit/test_tc176_compute_line_total_exact.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-176..TC-184 for full inputs/expected_output.
