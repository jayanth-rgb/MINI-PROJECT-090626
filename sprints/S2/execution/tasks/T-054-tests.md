# T-054 tests

| TC | AC | Asserts |
|----|----|---------|
| TC-076 | AC-039 | POST /api/v1/adjustments returns 201; final running_balance == physical_cb |
| TC-078 | AC-040 | POST with design having no active grade mappings → 422 with "no active grade" |

See [test_cases.md](../../design/test_cases.md).
