# T-048 tests

| TC | AC | Asserts |
|----|----|---------|
| TC-058 | AC-028 | Future sales_date → ValidationError |
| TC-059 | AC-028 | > 7 days prior → ValidationError |
| TC-060 | AC-029 | dealer.place snapshotted on header |
| TC-062 | AC-030 | Inactive verified_by_id → ValidationError |
| TC-063 | AC-031 | Inactive (design, grade) pair rejected |
| TC-065 | AC-033 | Ledger delta = -nos per line |

See [test_cases.md](../../design/test_cases.md).
