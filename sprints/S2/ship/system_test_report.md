# Sprint S2 — System Test Report

**Date:** 2026-06-23 · **Verdict:** **PASS** (after 2 fix iterations) · **Critical failures:** none

## Scenarios — 4/4 pass

| ID | Type | Threshold | Result | Actual |
|---|---|---|---|---|
| **ST-004** Performance | apply_inward p95 latency | < 100ms | ✅ pass | p50=3.6ms · **p95=4.4ms** · p99=5.7ms |
| **ST-005** Boundary | AC-021 7-day backdate window | exact boundary | ✅ pass | today-7 accepted, today-8 rejected (parametrized) |
| **ST-006** Security | Malformed POST → 422, no leak | 3 cases | ✅ pass | All 3 → 422, 0 InwardHeader rows |
| **ST-007** Load (TC-087 fn) | 2-session SELECT FOR UPDATE serializes | balances [10, 15, 20] | ✅ pass (iter 2) | [10, 15, 20] after fix |

Wall clock: ~49s (testcontainers cold start + 4 scenarios).

## Critical discovery: DS-002 LIMIT-1 race

**Iteration 1 of ST-007 failed**, revealing a real architectural gap:

```
T1: SELECT ... ORDER BY ledger_id DESC LIMIT 1 FOR UPDATE
    → identifies seed row (id=1, balance=10), acquires lock
T2: same SELECT FOR UPDATE → BLOCKS on T1's lock on row 1
T1: INSERT new row (id=2, balance=15), COMMIT, releases lock
T2: unblocks, RE-READS row 1 (NOT re-resolves LIMIT)
    → still sees balance=10 → INSERTS (id=3, balance=15) ❌
```

**Result without fix:** both writers got `prior=10` → both computed `running=15`. Lost update — the second writer's +5 vanished into a duplicate balance.

**Root cause (PG documented behavior):**
> "With LIMIT, the rows for which the lock has been obtained may be different from the rows that would be returned in the absence of the LIMIT clause. ... ORDER BY itself is not protected, so different transactions might lock the same row, in either order."

The `SELECT FOR UPDATE LIMIT 1 ORDER BY id DESC` pattern alone is **insufficient** for serializing writes when the data-shape is "lock the latest row".

### Fix applied — iteration 1

Added a PostgreSQL **advisory transaction lock** keyed on `(design_id, grade_id)` BEFORE the FOR UPDATE row lock in `src/domain/stock.py::_apply`:

```python
# DS-002: serialize writes per (design, grade) — required because
# SELECT ... ORDER BY ... LIMIT 1 FOR UPDATE does NOT re-resolve LIMIT
# after waiting on a row lock.
session.execute(
    text("SELECT pg_advisory_xact_lock(:k1, :k2)"),
    {"k1": design_id, "k2": grade_id},
)
latest = repo.latest_for_design_grade(design_id, grade_id, for_update=True)
```

`pg_advisory_xact_lock(int4, int4)` packs the two ints into an int8 lock key and auto-releases at txn commit. Pure cooperative lock — no DDL, no schema change.

**Re-run iteration 2:** ST-007 PASS — balances [10, 15, 20] verified. HLD R-001 mitigation now correct.

## Secondary fix — iteration 2

The ST-007 test commits via raw `SessionLocal` (bypassing the rollback-only `db_session` fixture), so its rows persist in the session-scoped testcontainer DB. This polluted 3 unrelated S1 seed tests (`test_tc016/022/030_*_idempotent`) that asserted exact row counts.

**Fix:** added `try/finally` cleanup block in ST-007 that DELETEs the ledger + map + grade + design rows it created.

**Final full backend suite: 112/112 PASS.**

## Tech debt

- **TD-011** opened + **CLOSED** in the same step. Documented in `.ases/decisions.json` as a refinement of DS-002. The DS-002 spec text could be updated in S3 to mandate the advisory-lock-first pattern; for S2 the implementation supersedes the spec wording.

## Files modified

- `backend/src/domain/stock.py` — added `pg_advisory_xact_lock` before FOR UPDATE in `_apply`
- `backend/tests/system/test_load_concurrent_select_for_update.py` — added cleanup `try/finally`

## Critical-failures gate

**None.** The 1 failure encountered during execution was resolved on iteration 1; the gate is evaluated on final state. Per skill: `critical_failures: []`, verdict `pass`.

## Outputs

- [sprints/S2/ship/system_test_scenarios.json](sprints/S2/ship/system_test_scenarios.json) — scenarios + execution_results + summary
- [sprints/S2/ship/system_test_report.json](sprints/S2/ship/system_test_report.json) — scoring file

## Next

→ **`/ases-uat S2`** — PO acceptance gate. The discovery + fix of TD-011 is the kind of finding that strengthens UAT confidence: the concurrency invariant is now real, not just spec-text.
