# T-044 tests

| TC | Asserts |
|----|---------|
| **TC-053** | `tbl_inward_line.CHECK(nos > 0)` fires `IntegrityError` violating `ck_inward_line_nos_positive` |
| **TC-064** | `tbl_sales_line.CHECK(nos > 0)` fires `ck_sales_line_nos_positive` |
| **TC-069** | `tbl_adjustment_header.CHECK(stock_date <= entry_date)` fires `ck_adjustment_header_dates` |
| **TC-088** | `tbl_stock_ledger.CHECK(source_type IN (…))` fires `ck_stock_ledger_source_type` |
| **TC-089** | FK `ON DELETE RESTRICT` from `tbl_inward_header.supplier_id` blocks hard DELETE of a referenced supplier |

See [test_cases.md](../../design/test_cases.md) for the full inputs/expected_output.
