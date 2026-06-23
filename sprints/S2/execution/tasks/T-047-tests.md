# T-047 tests

| TC | AC | Asserts |
|----|----|---------|
| TC-047 | AC-020 | Future purchase_date → ValidationError |
| TC-049 | AC-021 | > 7 days prior → ValidationError |
| TC-050 | AC-022 | Place snapshotted from supplier; master edits don't backfill |
| TC-051 | AC-023 | Line with inactive (design,grade) pair rejected |
| TC-054 | AC-025 | Lines with nos None/0 silently stripped |
| TC-055 | AC-026 | Zero valid lines → ValidationError |
| TC-056 | AC-027 | Atomic save: 1 header + N lines + N ledger rows |

See [test_cases.md](../../design/test_cases.md).
