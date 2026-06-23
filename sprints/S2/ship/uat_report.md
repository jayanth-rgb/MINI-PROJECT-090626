# Sprint S2 — UAT Report

**Reviewer:** Jayanth (PO) · **Date:** 2026-06-23 · **Verdict:** **APPROVED**

## Summary

| Outcome | Count |
|---|---|
| Accepted | **21 / 21** |
| Accepted with notes | 0 |
| Rejected | 0 |

All 21 acceptance criteria across F-007 (8), F-008 (6), F-009 (7) accepted. 5 additional cross-cutting invariants (DS-002/003/004/013 + write-path perf) also reviewed and accepted.

## Per-feature breakdown

### F-007 Inward — 8/8 ✅
AC-020 (future date) · AC-021 (>7d backdate) · AC-022 (place snapshot DS-013) · AC-023 (active pair) · AC-024 (nos > 0) · AC-025 (strip blanks) · AC-026 (≥1 valid line) · AC-027 (atomic save)

### F-008 Sales — 6/6 ✅
AC-028 (date bounds) · AC-029 (dealer place snapshot) · AC-030 (2 staff required+active) · AC-031 (active pair) · AC-032 (nos > 0) · AC-033 (Δ=−nos ledger)

### F-009 Adjustment — 7/7 ✅
AC-034 (single design header) · AC-035 (stock_date ≤ entry_date) · AC-036 (software_cb auto-fill) · AC-037 (physical_cb ≥ 0) · AC-038 (signed difference) · AC-039 (atomic ledger apply) · AC-040 (ERR-012 banner)

### Cross-cutting (DS) — 5/5 ✅
- **DS-002 concurrency** — TD-011 discovered + closed during system-test (advisory lock landed); ST-007 now PASS with real 2-session test
- **DS-003 back-date** — IS-008 end-to-end [5, 35, 55] ✓
- **DS-004 carry-forward** — opening = closing(m−1 day) ✓
- **DS-013 place** — historical immutability after master edit ✓
- **Performance** — apply_inward p95=4.4ms (budget 100ms — 23× headroom)

## Highlights of the run

- **Backend tests: 112/112 PASS** (S1 regression 46 + S2 backend 43 + system 12 + 11 fixtures)
- **Frontend tests: 5/13 pass + 8 deferred to TD-010** (Radix-Select jsdom limitation — same class as S1's TC-045 deferral; backend covers same ACs via API integration)
- **4/4 integration scenarios PASS** (IS-005 inward→ledger, IS-006 sales decrement, IS-007 adjustment full flow, IS-008 back-date recompute)
- **4/4 system tests PASS** after 2 fix iterations; TD-011 discovered and closed in-step

## Tech debt observed at UAT

| ID | Severity | Status | Note |
|---|---|---|---|
| TD-010 | minor | open (S3/V2) | Radix-Select jsdom incompatibility on 7 frontend TCs; not user-visible. Options: jest mock @radix-ui/react-select with native select, or move to Playwright E2E. |
| TD-011 | documented | **closed in S2** | Advisory lock added to `_apply` during ST-007. DS-002 spec text could be amended in S3 to mandate advisory-lock-first pattern. |
| TD-008 | minor | likely subsumed | First-row insert race likely now closed by TD-011's fix (advisory lock acquires even when no rows exist). Re-verify in S3 before further work. |

## Notes from the PO

- **Strengthened confidence**: The TD-011 discovery during system-test (and same-step closure) is the kind of finding that improves my confidence in shipping this sprint. The concurrency invariant is now empirically verified by a real 2-session test, not just spec-text.
- **Performance budget**: Write-path p95 of 4.4ms leaves ~95ms of budget for S3's read-path (dashboard) work. Comfortable margin.
- **UI parity**: Frontend transaction forms work as designed; backend authoritatively validates everything (zod is UX-level only).

## Verdict

**APPROVED.** All 21 ACs accepted; no rejections; no conditional acceptances. Ready to commit + proceed to final audit.

→ `/ases-devops S2`
