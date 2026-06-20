# Sprint S1 — System Test Report

**Executed:** 2026-06-20 · **Verdict:** **PASS** · **Critical failures:** 0

## Headline
- **3 / 3 executed scenarios pass** (14 test functions, all green, 23.8 s)
- **2 / 5 designed scenarios deferred** to S3 with explicit reasons (PRD performance NFRs and HLD R-001 stock-ledger race — both require M-003/M-004/M-005)
- **0 critical failures**

## Executed scenarios

| ID | Type | NFR / Risk | Threshold | Actual | Result |
|----|------|-----------|-----------|--------|--------|
| ST-001 | security | PRD non_functional.security | 7/7 malformed payloads → HTTP 422 | 7/7 returned 422; 0 5xx; 0 2xx | ✓ pass |
| ST-002 | security | HLD R-004 (V1 no-auth) | 6/6 GET endpoints reachable with no Authorization header | 6/6 returned 2xx; 0 401; 0 403 | ✓ pass |
| ST-003 | error_handling | HLD R-005 (soft-delete) | 4 soft-deleted rows remain SELECT-able + FKs resolve | 4/4 rows present, is_active=false, mapping FKs resolve | ✓ pass |

## Deferred scenarios

| ID | Type | NFR / Risk | Defer to | Why |
|----|------|-----------|----------|-----|
| ST-004 | performance | PRD non_functional.performance (dashboard < 1s; form save < 500ms; sales report < 2s) | S3 | Stock ledger (M-003) and reports (M-004/M-005) not yet delivered. `test_cases.json` `open_items_for_sprint_gate` explicitly notes this. |
| ST-005 | load | HLD R-001 (stock-ledger concurrent-write race) | S3 | `tbl_stock_ledger` and `apply_*()` functions not yet delivered. DS-002 `SELECT FOR UPDATE` mitigation can only be exercised once the ledger exists. |

Both deferrals are tracked explicitly so `/ases-final-audit`'s `risk_review` lens has the deferral on file rather than treating them as silent gaps.

## What the scenarios actually verify

- **ST-001 (security)** — The 7-variant matrix covers every empty-string violation across the 6 master entities. If a future PR weakens a Pydantic constraint (drops `min_length=1`, switches to `str | None`), the matching variant fails and the gate catches it.
- **ST-002 (R-004 non-regression)** — Verifies `main.py` did not introduce any auth middleware in S1. The trusted-network mitigation in DS-005 is documentation-side; this is the software-side complement.
- **ST-003 (R-005 mitigation)** — Critical for S2/S3: when transactions land, reports must join against master rows even if those masters were soft-deleted post-transaction. The 4-entity sweep proves the invariant holds across all relevant table types.

## Run command
```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/system/ -v
```

## Outputs
- [sprints/S1/ship/system_test_scenarios.json](sprints/S1/ship/system_test_scenarios.json) — design + execution annotations
- [sprints/S1/ship/system_test_report.json](sprints/S1/ship/system_test_report.json) — machine-readable verdict
- 3 test files under [backend/tests/system/](backend/tests/system/)

## Verdict
**PASS** — proceed to `/ases-uat S1`.
