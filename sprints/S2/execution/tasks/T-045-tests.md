# T-045 tests — 9 critical TCs

| TC | Asserts | Risk |
|----|---------|------|
| TC-079 | `closing_balance(as_of_date)` returns latest `running_balance` ≤ date | normal |
| TC-080 | `closing_balance` returns 0 with no rows | edge |
| TC-081 | `opening_balance(m_first) = closing_balance(m_first - 1)` | normal |
| TC-082 | `opening_balance` returns 0 for first month | edge |
| TC-083 | `apply_inward` writes +nos delta + correct running_balance | normal |
| TC-084 | `apply_sale` writes -nos delta | normal |
| TC-085 | `apply_adjustment` writes ±difference | normal |
| **TC-086** | **Back-dated insert triggers forward-recompute on later rows (HLD R-003)** | **HIGH** |
| **TC-087** | **Concurrent SELECT FOR UPDATE serializes writes (HLD R-001 / DS-002)** | **HIGH** |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.
