# T-052 tests

| TC | AC | Asserts |
|----|----|---------|
| TC-048 | AC-020 | POST /api/v1/inward with future date → 422 |
| TC-057 | AC-027 | POST /api/v1/inward returns 201; ledger running_balance accumulates across two POSTs |

See [test_cases.md](../../design/test_cases.md).
