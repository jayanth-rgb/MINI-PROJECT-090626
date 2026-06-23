# Sprint S2 — UAT Checklist

**Reviewer:** Jayanth (PO) · **Date:** 2026-06-23 · **Sprint goal:** Inward + Sales + Adjustment transaction forms with materialized stock ledger.

For each AC: [✓] accepted · [~] accepted_with_notes · [✗] rejected.
"System test result" links each AC to its verifying TC(s) and the green/yellow status from `test_run_report` + `system_test_report`.

---

## F-007 Inward (8 ACs)

[✓] **AC-020** (F-007): purchase_date in the future → ERR-001 rejection
    - How to verify: POST /api/v1/inward with `purchase_date = today+1` → 422 with detail mentioning "future"
    - Tests: TC-047 (service) · TC-048 (router) · TC-090 (UI zod) · ST-005 (boundary parametrized)
    - System test result: all PASS

[✓] **AC-021** (F-007): purchase_date older than today−7 → ERR-002 rejection
    - How to verify: POST with `purchase_date = today-8` → 422 mentioning "7 days"; today-7 accepted
    - Tests: TC-049 (service) · TC-091 (UI zod) · ST-005 (boundary inclusive/exclusive)
    - System test result: PASS — boundary exact

[✓] **AC-022** (F-007): place auto-populated from supplier, read-only
    - How to verify: UI shows place text auto-filled when supplier picked; place not editable; POST does not accept place in payload; saved header.place equals supplier.place at save time even if supplier later edits its place (DS-013)
    - Tests: TC-050 (service snapshot) · TC-092 (UI display) · IS-005 (end-to-end with header.place=='Mallur')
    - System test result: PASS

[✓] **AC-023** (F-007): Each line's (design, grade) must be in an active mapping
    - How to verify: POST with a deactivated pair → 422; UI renders only active grades for selected design
    - Tests: TC-051 (service) · TC-093 (UI grade-rows from getGrades)
    - System test result: PASS

[✓] **AC-024** (F-007): nos > 0 enforced (ERR-007)
    - How to verify: POST with nos=-1 → 422; UI rejects inline; DB CHECK fires if direct insert
    - Tests: TC-052 (Pydantic) · TC-053 (DB CHECK) · TC-094 (UI zod)
    - System test result: PASS

[✓] **AC-025** (F-007): blank/zero nos lines silently stripped
    - How to verify: POST with mix of [nos=10, nos=0, nos=None] → header persists with 1 line only
    - Tests: TC-054 (service)
    - System test result: PASS

[✓] **AC-026** (F-007): zero valid lines after stripping → ERR-008 rejection
    - How to verify: POST with all-blank nos → 422 mentioning "at least one line"; UI inline error
    - Tests: TC-055 (service) · TC-095 (UI)
    - System test result: PASS

[✓] **AC-027** (F-007): atomic save — 1 header + N lines + N ledger rows in one transaction
    - How to verify: After successful POST, all rows visible; on simulated failure, no partial state
    - Tests: TC-056 (service) · IS-005 (end-to-end count assertion)
    - System test result: PASS

---

## F-008 Sales (6 ACs)

[✓] **AC-028** (F-008): sales_date bounds — same as inward
    - Tests: TC-058 (service future) · TC-059 (service > 7d) · TC-096 (UI zod future)
    - System test result: PASS

[✓] **AC-029** (F-008): place auto-populated from dealer, read-only (DS-013 mirror)
    - Tests: TC-060 (service snapshot) · IS-006 (end-to-end)
    - System test result: PASS

[✓] **AC-030** (F-008): BOTH loading_staff_id AND verified_by_id required AND active
    - How to verify: POST with missing or inactive verified_by → 422; UI inline errors on either field
    - Tests: TC-061 (Pydantic both required) · TC-062 (service inactive verified_by) · TC-097 (UI required check)
    - System test result: PASS

[✓] **AC-031** (F-008): (design, grade) pair active check
    - Tests: TC-063 (service)
    - System test result: PASS

[✓] **AC-032** (F-008): nos > 0 enforced — same enforcement chain as AC-024
    - Tests: TC-064 (DB CHECK on sales_line)
    - System test result: PASS

[✓] **AC-033** (F-008): ledger row written with delta = −nos (sale decrements)
    - Tests: TC-065 (service) · TC-066 (router 201 + ledger decrease) · IS-006 (end-to-end balance 50 → 38)
    - System test result: PASS

---

## F-009 Adjustment (7 ACs)

[✓] **AC-034** (F-009): exactly one design per adjustment — design_id on header, not line
    - How to verify: Pydantic AdjustmentLineCreate has no design_id field; AdjustmentCreate header has design_id
    - Tests: TC-067 (Pydantic structural)
    - System test result: PASS

[✓] **AC-035** (F-009): stock_date ≤ entry_date (ERR-010)
    - How to verify: Pydantic + service + DB CHECK all reject stock>entry
    - Tests: TC-068 (Pydantic) · TC-069 (DB CHECK) · TC-098 (UI zod cross-field)
    - System test result: PASS

[✓] **AC-036** (F-009): software_cb auto-populated as of stock_date per grade
    - How to verify: GET /designs/{id}/grades-with-cb?stock_date= returns [{grade_id, grade_code, software_cb}] correctly; AdjustmentForm pre-fills the read-only field
    - Tests: TC-070 (service) · TC-071 (router) · TC-099 (UI) · IS-007 (end-to-end seed→GET→POST)
    - System test result: PASS

[✓] **AC-037** (F-009): physical_cb ≥ 0 (zero valid)
    - Tests: TC-072 (Pydantic −1 rejected) · TC-073 (Pydantic 0 accepted) · TC-100 (UI zod)
    - System test result: PASS

[✓] **AC-038** (F-009): difference = physical_cb − software_cb (signed)
    - Tests: TC-074 (service signed difference) · TC-101 (UI live computation)
    - System test result: PASS

[✓] **AC-039** (F-009): apply ledger atomically with delta = difference
    - How to verify: After save, ledger has new row with delta=difference; zero-difference lines still persist audit row but skip ledger write
    - Tests: TC-075 (service) · TC-076 (router) · IS-007 (zero-diff optimization verified)
    - System test result: PASS

[✓] **AC-040** (F-009): design without active grade combinations → ERR-012
    - How to verify: POST adjustment for such a design → 422; UI shows Err012Banner + disabled submit
    - Tests: TC-077 (service) · TC-078 (router) · TC-102 (UI banner)
    - System test result: PASS

---

## Cross-cutting verifications (not AC-bound but PO-relevant)

[✓] **DS-002 concurrency** — 2-session apply_inward serialization via `pg_advisory_xact_lock` + `SELECT FOR UPDATE`
    - Test: ST-007 (2-thread concurrency, real PG)
    - **Discovery + fix during system-test:** TD-011 found and closed in-step (advisory lock added to `_apply`). Without this, two concurrent first-saves on same (design, grade) would have lost an update.
    - System test result: PASS (iteration 2)

[✓] **DS-003 back-date forward-recompute** — bounded by AC-021 7-day window
    - Tests: TC-086 (domain unit) · IS-008 (end-to-end [5, 35, 55])
    - System test result: PASS

[✓] **DS-004 carry-forward** — opening_balance = closing_balance(month_first − 1 day)
    - Tests: TC-080, TC-081, TC-082 (domain)
    - System test result: PASS

[✓] **DS-013 place denormalization** — historical immutability after master edit
    - Tests: TC-050 verifies (mutates master after save, asserts header unchanged)
    - System test result: PASS

[✓] **Write-path performance** — single apply_inward p95 = 4.4ms (budget 100ms)
    - Test: ST-004
    - System test result: PASS — 23× under budget

---

## Notes / tech debt observed

| ID | Severity | Status | Note |
|---|---|---|---|
| TD-010 | minor | open (S3/V2) | 7 frontend tests can't exercise Radix Select in jsdom; covered transitively by backend API tests + UI scaffold. No user-visible impact. |
| TD-011 | documented | **closed in S2** | Discovered + fixed during system-test; advisory lock pattern added to `_apply`. Strengthens DS-002. |
| TD-008 | minor | open (V2) | First-row insert race (theoretical, once per (design, grade) lifetime). Now subsumed by TD-011's advisory lock — the lock acquires even when no row exists, so this is also effectively closed. Worth re-verifying in S3 before further work. |

---

## Verdict

**APPROVED** — all 21 ACs accepted; 5 cross-cutting verifications accepted. The TD-011 discovery + closure during system-test is a positive — the concurrency invariant is now empirically verified, not just spec-text.

→ `/ases-devops S2`
