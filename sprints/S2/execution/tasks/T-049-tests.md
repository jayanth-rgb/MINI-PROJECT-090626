# T-049 tests

| TC | AC | Asserts |
|----|----|---------|
| TC-074 | AC-038 | `difference = physical_cb - software_cb`; negative differences are negative (no abs) |
| TC-075 | AC-039 | Ledger row written with delta = difference, running_balance = software_cb + difference |
| TC-077 | AC-040 | Design with no active grade mappings → ValidationError ERR-012 |

See [test_cases.md](../../design/test_cases.md).
