# T-046 tests

| TC | Asserts |
|----|---------|
| TC-052 | `InwardLineCreate` rejects `nos = -1` |
| TC-061 | `SalesCreate` rejects payload missing `loading_staff_id` |
| TC-067 | `AdjustmentCreate` places `design_id` on the header (single) — lines share one design |
| TC-068 | `AdjustmentCreate` rejects `stock_date > entry_date` via model_validator |
| TC-072 | `AdjustmentLineCreate` rejects `physical_cb = -1` |
| TC-073 | `AdjustmentLineCreate` accepts `physical_cb = 0` (zero is valid) |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.
