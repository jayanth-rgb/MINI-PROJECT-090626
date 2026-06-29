# Sprint S3 — UAT Report

**Reviewer:** Jayanth (PO) · **Date:** 2026-06-29 · **Verdict:** **APPROVED**

All 13 ACs accepted on first review. Zero rejected, zero conditional.

## AC review summary

| Feature | ACs | Accepted | With Notes | Rejected |
|---|---:|---:|---:|---:|
| F-010 Stock Dashboard | 5 | 5 | 0 | 0 |
| F-011 Sales Report | 5 | 5 | 0 | 0 |
| F-012 Carry-Forward | 3 | 3 | 0 | 0 |
| **Total** | **13** | **13** | **0** | **0** |

## Per-AC verdicts

| AC | Feature | Status | Verifying tests |
|---|---|---|---|
| AC-041 | F-010 | ✓ accepted | TC-115, TC-117, TC-129, TC-130, TC-150, IS-009, ST-012 |
| AC-042 | F-010 | ✓ accepted | TC-118, TC-154 |
| AC-043 | F-010 | ✓ accepted | TC-119, TC-127, TC-153, IS-012 |
| AC-044 | F-010 | ✓ accepted | TC-120, TC-121, TC-128, IS-009 |
| AC-045 | F-010 | ✓ accepted | TC-122, **ST-008 (p95=33.1ms — 24× headroom)** |
| AC-046 | F-011 | ✓ accepted | TC-133..136, TC-143, TC-144, TC-147, TC-148, IS-010 |
| AC-047 | F-011 | ✓ accepted | TC-137, TC-138, TC-146, IS-010 |
| AC-048 | F-011 | ✓ accepted | TC-139, IS-010 |
| AC-049 | F-011 | ✓ accepted | TC-140 (UI layer to ship via `/ases-ui-scaffold S3` — not a backend UAT blocker) |
| AC-050 | F-011 | ✓ accepted | TC-141, TC-142, TC-145, IS-010 (DS-017 makes violation structurally impossible) |
| AC-051 | F-012 | ✓ accepted | TC-153, **IS-012** (end-to-end HTTP cross-month) |
| AC-052 | F-012 | ✓ accepted | TC-154 |
| AC-053 | F-012 | ✓ accepted | TC-155, TC-156 (+ S2 IS-008 for `_recompute_forward`) |

## Cross-cutting review (all accepted)

| ID | Topic | Note |
|---|---|---|
| **DS-015** | Advisory-lock-first writes (amends DS-002) | Inherited from S2; not re-exercised in S3 |
| **DS-016** | Single GROUP BY for dashboard | Verified via TC-123..126 + ST-008 perf |
| **DS-017** | Shared filter predicate for sales report | AC-050 reconciliation guaranteed structurally + at runtime |
| **ST-008** perf | Dashboard p95 = 33.1 ms | ~24× headroom under PRD "sub-second" |
| **ST-009** perf | Sales Report p95 = 715.7 ms over 10,800 sales lines | ~2.8× headroom under 2s PRD target |
| **ST-010** security | SQL-injection across all 3 list filters | All neutralized; tbl_sales_header intact |
| **ST-011** security | V1 no-auth posture for new endpoints | Verified (intentional V1 contract per DS-005) |
| **ST-012** boundary | Soft-delete cascade (R-005) | Dashboard hides deactivated pair; sales report retains historical FK joins |

## Tech debt status

| ID | Status | Severity | Target | Note |
|---|---|---|---|---|
| **CF-001** | open | minor | PO action (not blocking) | PG bring-up still pending from S1 W5; testcontainers covered everything |
| **TD-001** | open | minor | `/ases-ui-scaffold S3` | shadcn calendar classNames patch |
| **TD-010** | open | minor | `/ases-ui-design S3` | Radix Select/Popover jsdom incompatibility |
| **TD-008** | open (V2) | minor | V2 | First-row insert race; theoretical, acceptable for V1 |

**No NEW tech debt introduced by S3.** All 4 entries above are pre-existing carry-forwards.

## Phase 3 test totals

| Suite | Count | Result |
|---|---:|---|
| Unit + integration pytest | 158 | **158 PASS** |
| Integration scenarios (IS-005..IS-012) | 8 | **8 PASS** |
| System test scenarios (S1+S2+S3 — ST-001..ST-012) | 12 | **12 PASS** |
| **Total** | **178** | **178 PASS** |

- **Regressions:** 0
- **Fix iterations during Phase 3:** 2 (both test-side seed bugs — TC-142/TC-122 + IS-011/IS-012 dates). Production source was not modified at any point during Phase 3.

## Notes
- 178 tests green across the full project history (S1+S2+S3) with substantial performance and security headroom.
- DS-015/016/017 collectively turn the AC-050 reconciliation invariant and DS-016 dashboard formula into structural correctness properties — the runtime assertions are defense-in-depth.
- No production code was modified during Phase 3 — every failure was caught by the existing AC-021 7-day window or by FORMULA-001 / AC-050 server-side invariants, then fixed on the test side.

## Verdict

**APPROVED.** Ready for `/ases-devops S3`.

**Signed:** Jayanth (PO) · 2026-06-29
