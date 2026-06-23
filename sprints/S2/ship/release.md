# Sprint S2 — Release

**Released:** 2026-06-23 · **Commit:** `68a675e` · **Verdict:** 🟢 SHIP

## What shipped

| Feature | ACs | Pass | Backend tasks | UI |
|---|---|---|---|---|
| **F-007 Inward Entry** | 8 | 8/8 | T-042, T-043, T-045, T-047, T-051, T-052 | InwardForm + page |
| **F-008 Sales Entry** | 6 | 6/6 | T-042, T-043, T-045, T-048, T-051, T-053 | SalesForm + page |
| **F-009 Stock Adjustment** | 7 | 7/7 | T-042, T-043, T-045, T-049, T-050, T-051, T-054, T-055 | AdjustmentForm + AdjustmentLineRow + Err012Banner + page |

**21 / 21 ACs accepted.** 16 backend tasks all CLEAN on iteration 1.

## Verification

| Layer | Result |
|---|---|
| Backend pytest | **112 / 112 PASS** (S1 regression 46 + S2 backend 43 + system 12 + fixtures 11) |
| Integration scenarios | **4 / 4 PASS** (IS-005..IS-008) |
| System tests | **4 / 4 PASS** after TD-011 in-step fix |
| Frontend jest | 5 / 13 PASS + 7 deferred (TD-010 Radix-jsdom — same class as S1's TC-045) |
| UAT | **APPROVED — 21/21** |

## New architectural decisions

- **DS-013** — Denormalize `place` onto `tbl_inward_header` + `tbl_sales_header` (snapshot at save). Eliminates 1 JOIN on S3's Sales Report hot path; preserves historical immutability.
- **DS-014** — TimestampMixin → TIMESTAMPTZ; migration 0003 ALTERs 4 S1 columns. **Closes TD-007.**

## Tech debt accounting

| ID | Status | Note |
|---|---|---|
| TD-005 | open (W5) | S1 carry-over — PG bring-up pending |
| TD-006 | open (W5) | S1 carry-over — seed verification pending |
| TD-007 | **closed_in_S2** | by DS-014 |
| TD-008 | open (V2) | First-row race — likely subsumed by TD-011 fix; re-verify in S3 |
| TD-009 | **closed_in_S2** | 6 frontend zod-only TCs implemented at /ases-test-impl |
| TD-010 | open (S3/V2) | 7 frontend tests deferred (Radix-jsdom infra) |
| TD-011 | **closed_in_S2** | Advisory lock added to `_apply` during /ases-system-test |

**Net open after S2:** 4 (2 W5-blocked S1 carry, 1 V2 likely-subsumed, 1 frontend infra)

## Headline discoveries

1. **16 / 16 backend tasks CLEAN on iteration 1** — first sprint with zero-iteration backend dev
2. **TD-011 discovered + closed in-step** during system-test: PG `SELECT FOR UPDATE LIMIT 1 ORDER BY ...` doesn't re-resolve LIMIT after waiting on a row lock; the safe pattern requires advisory-lock-first. Empirically verified by 2-session test (ST-007).
3. **Write-path performance 23× under budget** (p95=4.4ms vs 100ms budget) — leaves S3 read-path with ample latency budget
4. **DS-002 spec text refinement recommended for S3** — current text describes only the FOR UPDATE primitive; the verified safe layered pattern (advisory lock + FOR UPDATE) should be in the spec to prevent future regressions

## Roadmap progress

| Sprint | Status | Verdict | Commit |
|---|---|---|---|
| S1 Data Foundation | shipped | SHIP | 571c601 |
| **S2 Transaction Forms + Stock Ledger** | **shipped** | **SHIP** | **68a675e** |
| S3 Reporting & Carry-Forward | planned | — | — |

## Updates to long-lived state

| File | Change |
|---|---|
| `CHANGELOG.md` | S2 entry prepended (newest first) |
| `contracts/roadmap.json` | S2 marked shipped + commit + verdict + new_decisions[] |
| `.ases/global_context.json` | +SP-002, +FT-007/008/009, +TD-008/010/011, +RI-003; TD-007 marked closed_in_S2 |
| `.ases/context.json` | Phase SPRINT_SHIP → SPRINT_DESIGN; current_sprint S2 → S3; sprint_history S2 entry already stamped by sprint-close (now reaffirmed by release) |

## Suggested S3 PRD/decisions updates

The next `/ases-prd-update S3` (optional) or `/ases-lld S3` should consider:

1. **AC-045** — restate "sub-second dashboard latency" as numeric `p95 < 500ms` so `/ases-system-test S3` can assert.
2. **DS-002 text amendment** — mandate the advisory-lock-first layered pattern (closes FA-S2-002/003 + RI-003 + reduces future regression risk).
3. **TD-008 decision** — PRD-level choice: accept first-row race as V1, or require V2 mitigation. Likely already addressed by TD-011 fix; spec-level decision still cleaner.

## Sprint cycle: **complete**

→ Return to Phase 1 Sprint Design for S3:
```
/ases-prd-update S3   (optional)
/ases-lld S3          (start S3 design)
```
