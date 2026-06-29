# Sprint S3 — Task DAG (T-057 → T-066)

**10 backend tasks** decomposing the S3 LLD into per-file work units. Zero UI tasks — frontend pages ship via the UI track (`/ases-ui-design S3`).

## DAG (parallel groups in execution order)

```
Group A (parallel — 4 tasks, no inter-deps):
  T-057  schemas/dashboard.py            [create · M-004]
  T-058  schemas/sales_report.py         [create · M-005]
  T-059  repositories/ledger_aggregates  [create · M-004]
  T-060  repositories/master.py          [modify · M-001]

Group B (parallel — 2 tasks, both unblock once A is done):
  T-061  services/dashboard_service      [create · M-004]  ← T-057, T-059, T-060
  T-062  services/sales_report_service   [create · M-005]  ← T-058

Group C (serial gate):
  T-063  presentation/api/dependencies   [modify · M-002]  ← T-061, T-062

Group D (parallel — 2 routers):
  T-064  routers/dashboard.py            [create · M-004]  ← T-057, T-061, T-063
  T-065  routers/sales_report.py         [create · M-005]  ← T-058, T-062, T-063

Group E (final wiring):
  T-066  main.py                         [modify · M-002]  ← T-064, T-065
```

## Linear execution order
`T-057 → T-058 → T-059 → T-060 → T-061 → T-062 → T-063 → T-064 → T-065 → T-066`

## Task → file → TC count

| Task | File | Type | TCs | Module |
|---|---|---|---|---|
| T-057 | `presentation/schemas/dashboard.py` | create | 0 (test_required=false; covered transitively) | M-004 |
| T-058 | `presentation/schemas/sales_report.py` | create | 0 (test_required=false; covered transitively) | M-005 |
| T-059 | `infrastructure/db/repositories/ledger_aggregates.py` | create | 4 (TC-123..126) | M-004 |
| T-060 | `infrastructure/db/repositories/master.py` | **modify** | 3 (TC-150..152) | M-001 |
| T-061 | `application/services/dashboard_service.py` | create | 11 (TC-115/116/118-122/127-129/156) | M-004 |
| T-062 | `application/services/sales_report_service.py` | create | 14 (TC-133..139/141-146/157) | M-005 |
| T-063 | `presentation/api/dependencies.py` | **modify** | 2 (TC-159/160) | M-002 |
| T-064 | `presentation/api/routers/dashboard.py` | create | 4 (TC-117/130/131/132) | M-004 |
| T-065 | `presentation/api/routers/sales_report.py` | create | 5 (TC-140/147/148/149/158) | M-005 |
| T-066 | `main.py` | **modify** | 0 (verified via T-063's TC-159/160 integration tests) | M-002 |

**TC reconciliation**: 43 TCs mapped to tasks + 3 unmapped TCs (TC-153, TC-154, TC-155 — F-012 carry-forward verifications against the existing S2 `domain/stock.py`, authored at `/ases-test-impl S3` only — no new dev task) = **46 total**. Matches `test_cases.json`.

## Decisions in scope
DS-002 (advisory-lock-first concurrency, inherited from S2) · DS-003 (running_balance materialization) · DS-004 (opening_balance = closing(prev-day)) · DS-007 · DS-013 (denormalized snapshots in transaction tables) · DS-015 (advisory-lock-first writes, S2-amend) · DS-016 (single GROUP BY for dashboard aggregation) · DS-017 (shared filter predicate for sales-report dual-payload).

## UI track handoff
`ui_tasks = []`. The UI track produces `/admin/dashboard/` + `/admin/reports/sales/` (Next.js pages + components + api wrappers + types) against this task list's API surface:

- `GET /api/v1/dashboard?as_of_date=YYYY-MM-DD` (T-064)
- `GET /api/v1/reports/sales?date_from=&date_to=&dealer_ids=&places=&design_ids=` (T-065)
- Existing S1 `GET /api/v1/designs`, `GET /api/v1/dealers` (filter dropdowns)
- Existing S2 `GET /api/v1/sales` (places derivation if needed)

## Next
- Batch path: `/ases-batch-exec S3` (per-task sub-agent dispatch — recommended at S3 size)
- Per-task path: `/ases-validate T-057 S3` → `/ases-dev T-057 S3` → `/ases-critique T-057 S3` → repeat
- UI path (parallel-eligible after T-064 + T-065 land): `/ases-ui-design S3`
