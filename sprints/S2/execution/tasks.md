# Sprint S2 — Task DAG

**Sprint:** S2 · **Total backend tasks:** 16 (T-041..T-056) · **UI tasks:** delivered via UI track
**ID convention:** continuing from S1 (TC-001..TC-040; S2 = T-041..T-056)

## DAG visualization

```
Phase A (parallel):  T-041 (base.py)        T-046 (schemas)
                          │
                          ▼
Phase B:             T-042 (ORM models)
                          │
                          ├─────────────────┐
                          ▼                 ▼
Phase C (parallel):  T-043 (repositories)   T-044 (migration 0003)
                          │
                          ▼
Phase D:             T-045 (domain/stock)     ← highest-risk file
                          │
                          ├─────────────────┬─────────────────┐
                          ▼                 ▼                 ▼
Phase E (parallel):  T-047 (inward svc)  T-048 (sales svc)  T-049 (adjust svc)  T-050 (cb svc)
                          │
                          ▼
Phase F:             T-051 (dependencies.py)
                          │
                          ├─────────────────┬─────────────────┐
                          ▼                 ▼                 ▼
Phase G (parallel):  T-052 (inward router)  T-053 (sales)  T-054 (adjust)  T-055 (designs MODIFY)
                          │
                          ▼
Phase H:             T-056 (main.py — mount 3 new routers)
```

8 parallel groups; critical path is 8 tasks long.

## Task table

| ID | File | Type | depends_on | TCs |
|----|------|------|------------|-----|
| T-041 | infrastructure/db/base.py | modify | — | — |
| T-042 | infrastructure/db/models/transactions.py | create | T-041 | — |
| T-043 | infrastructure/db/repositories/transactions.py | create | T-042 | — |
| T-044 | db/migrations/versions/0003_transaction_and_ledger_tables.py | create | T-041, T-042 | TC-053, 064, 069, 088, 089 |
| T-045 | domain/stock.py | create | T-043 | TC-079..TC-087 (9 critical TCs) |
| T-046 | presentation/schemas/transactions.py | create | — | TC-052, 061, 067, 068, 072, 073 |
| T-047 | application/services/inward_service.py | create | T-043, T-045, T-046 | TC-047, 049, 050, 051, 054, 055, 056 |
| T-048 | application/services/sales_service.py | create | T-043, T-045, T-046 | TC-058, 059, 060, 062, 063, 065 |
| T-049 | application/services/adjustment_service.py | create | T-043, T-045, T-046 | TC-074, 075, 077 |
| T-050 | application/services/design_grade_cb_service.py | create | T-045, T-046 | TC-070 |
| T-051 | presentation/api/dependencies.py | modify | T-047..T-050 | — |
| T-052 | presentation/api/routers/inward.py | create | T-051 | TC-048, 057 |
| T-053 | presentation/api/routers/sales.py | create | T-051 | TC-066 |
| T-054 | presentation/api/routers/adjustments.py | create | T-051 | TC-076, 078 |
| T-055 | presentation/api/routers/designs.py | modify | T-051, T-050 | TC-071 |
| T-056 | main.py | modify | T-052..T-055 | — |

## Gap mapping

| Gap / Risk | Task |
|------------|------|
| **TD-007** TIMESTAMPTZ uplift | T-041 + T-044 |
| **HLD R-001** stock-ledger concurrent-write race (DS-002 SELECT FOR UPDATE) | T-045 |
| **HLD R-003** back-dated transaction recompute (DS-003) | T-045 |
| **DF-003 contract** GET /designs/{id}/grades-with-cb | T-050 + T-055 |

## Test-case coverage

43 backend TCs covered by these tasks (TC-047..TC-089). The remaining 13 TCs (TC-090..TC-102) cover the 3 frontend forms and ship via the UI track.

## Highest-risk task: **T-045** `domain/stock.py`

Contains the entire ledger arithmetic chain:
- `apply_inward / apply_sale / apply_adjustment` — SELECT FOR UPDATE + insert + (if back-dated) forward-recompute
- `closing_balance(as_of_date)` — O(1) lookup driving Adjustment form pre-population AND S3 Dashboard
- `opening_balance(month_first)` — derived from closing_balance(month_first - 1)
- `_recompute_forward` — replays deltas on later rows after a back-dated insert

Recommend extra critique attention; carries 9 critical TCs including TC-086 (back-date) and TC-087 (concurrency).

## Frontend UI track

Not in this DAG. The 3 transaction-form UIs are produced by:
1. `/ases-ui-design S2` — Gemini designs the UI spec
2. `/ases-ui-review S2` — Opus validates against PRD ACs
3. `/ases-ui-scaffold S2` — Gemini builds the standalone scaffold; integration_points list the API contracts above
4. UI tasks then enter the per-task tests via `/ases-test-impl S2` for TC-090..TC-102

The backend DAG is independent of the UI track — they may proceed in parallel.

## Next step
→ Pipeline branches:
- **UI track:** `/ases-ui-design S2` (designs ui_spec.json; needs S2 LLD + integration_points)
- **Backend track:** `/ases-validate T-041 S2` to start the dev loop on the leftmost parallel-group entry

Both can run concurrently. UI track APPROVED gates the eventual frontend test pass; backend completion gates `/ases-test-run S2`.
