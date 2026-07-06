# T-080 tests — repositories/pricing.py (TC-187..TC-189)

Integration tests requiring PostgreSQL (testcontainers).

| TC | Method | Setup | Expected |
|---|---|---|---|
| TC-187 | `get_active_price(1, 1)` on 2026-07-02 | 2 active prices: 100.00 effective 2026-01-01, 120.00 effective 2026-06-01 | Returns price with unit_price=120.00, effective_from=2026-06-01 |
| TC-188 | `get_active_price(1, 1)` | 1 price row with is_active=False | Returns `None` |
| TC-189 | `create_with_lines(header_data, [line_dict])` | sales_header exists | Returns InvoiceHeaderModel with invoice_number, total_amount=500.00, lines loaded, lines[0].line_total=500.00 |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc187_price_repo_get_active_price.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-187..TC-189 for full inputs/expected_output.
