# Sprint S3 — UAT Checklist

**Reviewer:** Jayanth (PO) · **Date:** 2026-06-29 · **Sprint goal:** Stock Dashboard (F-010), Sales Report (F-011), Monthly Carry-Forward verification (F-012) — read-side completion on top of the materialized stock ledger and denormalized place snapshots from S2.

For each AC mark **[✓] accepted · [~] accepted_with_notes · [✗] rejected**.
"System test result" links each AC to its verifying TC(s) and the green/yellow status from `test_run_report.json` + `system_test_report.json` + `integration_scenarios.json`.

How to verify (before marking each row): start the running system in another terminal and exercise the endpoint:

```bash
# Terminal 1 — bring up PG (if not already)
cd 'e:/MY NEW MINI PROJECT/MINI PROJECT 090626' && docker-compose up -d db

# Terminal 2 — run backend (separate from test harness)
cd backend && .venv/Scripts/python.exe -m uvicorn src.main:app --reload --port 8000

# Terminal 3 — manually exercise endpoints with curl / Postman / browser:
curl 'http://localhost:8000/api/v1/dashboard?as_of_date=2026-06-29'
curl 'http://localhost:8000/api/v1/reports/sales'
```

(Or — if the long-lived PG bring-up is still pending W5/CF-001 — rely on the testcontainers-backed test report below. **All 158 unit/integration tests and 5 system-test scenarios passed** under testcontainers PG.)

---

## F-010 — Stock Dashboard (5 ACs)

[✓] **AC-041** (F-010): Selecting a date returns one row per (active design, active grade combination) with Opening, Inward, Outward, Adjust, Closing columns as defined in FORMULA-001.
- How to verify: GET /api/v1/dashboard?as_of_date=YYYY-MM-DD → returns list of objects with the 10 fields; only active pairs included; FORMULA-001 (opening + inward − outward + adjust == closing) holds per row (server asserts; manually verify too).
- Tests: TC-115, TC-117, TC-129, TC-130, TC-150 · IS-009 (full HTTP) · ST-012 (active/inactive cascade)
- System test result: **PASS** (5/5 integration, dashboard cascade verified)

[ ] **AC-042** (F-010): Opening balance for the first month of system use is zero (FORMULA-002).
- How to verify: With no ledger history, GET /api/v1/dashboard?as_of_date=<first-of-month> → opening=0 for every row.
- Tests: TC-118, TC-154
- System test result: **PASS**

[ ] **AC-043** (F-010): On the first day of any subsequent month, Opening = Closing of last day of previous month with no manual action.
- How to verify: Inward of 200 on May 28; GET /api/v1/dashboard?as_of_date=2026-06-01 (or any June date) → row.opening == 200 with no separate "month rollover" call. Same fact reproduced via HTTP in IS-012.
- Tests: TC-119, TC-127, TC-153 · **IS-012** (cross-month carry-forward through full HTTP stack)
- System test result: **PASS**

[ ] **AC-044** (F-010): Closing balance for any date equals Opening + cumulative Inward − cumulative Outward + cumulative Adjust within the current month up to that date.
- How to verify: Server-side `assert opening + inward − outward + adjust == closing` runs on every row of every /dashboard response; absence of `AssertionError` over the test suite is the proof. Spot-check by hand on the running system if desired.
- Tests: TC-120, TC-121, TC-128 · IS-009 (E2E HTTP)
- System test result: **PASS**

[ ] **AC-045** (F-010): Dashboard response is sub-second for any single date with up to 12 months of accumulated transactions.
- How to verify: ST-008 measured **p95 = 33.1 ms (p50 = 24.8 ms)** over 30 samples through the full HTTP stack with 2016 ledger rows (6 active pairs × 12 months × 28 txns/month). Headroom: ~24× under the 800 ms working threshold, ~30× under the PRD "sub-second" bar.
- Tests: TC-122 (service-layer) · **ST-008 (HTTP perf gate)**
- System test result: **PASS** with substantial headroom

---

## F-011 — Sales Report (5 ACs)

[ ] **AC-046** (F-011): All filters are optional and multi-select; no filters = full dataset (RULE-018).
- How to verify: GET /api/v1/reports/sales (no params) returns full dataset; GET with `?dealer_ids=1&dealer_ids=2&places=Mysuru&places=Bengaluru&date_from=...&date_to=...&design_ids=1&design_ids=2` returns multi-select intersection.
- Tests: TC-133, TC-134, TC-135, TC-136, TC-143, TC-144, TC-147, TC-148 · IS-010
- System test result: **PASS**

[ ] **AC-047** (F-011): Consolidation Report groups by design_id + grade_id, sums nos, ordered by design_name ASC then grade_code ASC (RULE-019 / FORMULA-004).
- How to verify: Inspect `consolidation[]` in the response — single row per (design, grade); total_nos = SUM(line.nos) for that group; ordering verified by manual eye against seeded sample.
- Tests: TC-137, TC-138, TC-146 · IS-010
- System test result: **PASS**

[ ] **AC-048** (F-011): Transaction Report returns each sales line matching filters, ordered by sales_date ASC (RULE-020).
- How to verify: Inspect `transactions[]` — one entry per matching sales_line; ascending by sales_date then header_id.
- Tests: TC-139 · IS-010
- System test result: **PASS**

[ ] **AC-049** (F-011): Both sections render together on the same screen on every filter apply — no toggle, no tab, Consolidation first.
- How to verify: Single GET returns `{consolidation, transactions}` in one JSON body — Consolidation FIRST in the object key order. (UI layer to surface both together — deferred to /ases-ui-scaffold S3.)
- Tests: TC-140
- System test result: **PASS** (backend contract; UI verification at /ases-ui-scaffold S3)

[ ] **AC-050** (F-011): Sum of Numbers across all rows of Transaction Report for any filter set equals the sum of Numbers in Consolidation Report for the same filter set.
- How to verify: For any GET response, `sum(transactions[*].nos) == sum(consolidation[*].total_nos)`. Server asserts this; client may verify too.
- Tests: TC-141, TC-142, TC-145 · IS-010 (E2E HTTP, 4-filter intersection)
- System test result: **PASS** (DS-017 shared filter predicate makes violation structurally impossible; runtime assertion is defense-in-depth)

---

## F-012 — Monthly Stock Carry-Forward (3 ACs)

[ ] **AC-051** (F-012): On the first transaction touching a (design, grade) in Month N+1, Opening = Closing as of last day of Month N (FORMULA-002).
- How to verify: Inward of 200 in May; GET /api/v1/dashboard?as_of_date=<June-date> → row.opening == 200. **IS-012** verifies this through the full HTTP stack relative to today.
- Tests: TC-153 · **IS-012**
- System test result: **PASS**

[ ] **AC-052** (F-012): When no prior month data exists for a (design, grade), Opening = 0 (RULE-012).
- How to verify: For a pair with no historical ledger, dashboard.opening == 0 in any month.
- Tests: TC-154
- System test result: **PASS**

[ ] **AC-053** (F-012): Carry-forward must remain correct after a back-dated transaction inside the 7-day window straddles a month boundary.
- How to verify: Inward in early June dated back to May 31 (within 7 days) triggers `domain.stock._recompute_forward`; dashboard for any later June date reflects the corrected opening.
- Tests: TC-155, TC-156 (covers the recompute_forward path end-to-end)
- System test result: **PASS** (and S2 IS-008 covers the recompute itself)

---

## Cross-cutting items (for context, not separate UAT marks)

| ID | Topic | Status |
|---|---|---|
| **DS-015** | Advisory-lock-first stock-ledger writes (amends DS-002) | inherited from S2; not re-exercised in S3 (read-only sprint) |
| **DS-016** | Single CASE-aggregated GROUP BY for dashboard | verified via TC-123/124/125/126 + ST-008 perf |
| **DS-017** | Shared filter predicate for sales-report dual-payload | verified structurally + via AC-050 runtime assert (TC-141/142, IS-010) |
| **ST-010** | SQL-injection protection across all 3 list-type filters | PASS |
| **ST-011** | V1 no-auth posture for both new endpoints | PASS (intentional V1 contract per DS-005) |
| **ST-012** | Soft-delete cascade (R-005) | PASS — dashboard hides deactivated pair; sales report retains historical FK-joined sales |

---

## Carry-forward issues (not blocking S3 UAT)

| ID | What | Owner | Notes |
|---|---|---|---|
| CF-001 | PO bring-up of long-lived PG + alembic upgrade + seed | PO | Not blocking; testcontainers covered all S3 tests. Required for manual API smoke. |
| TD-001 | shadcn calendar.tsx classNames patch | `/ases-ui-scaffold S3` | UI-track item, surfaces at UI scaffold |
| TD-010 | Radix Select/Popover jsdom incompatibility | PO + `/ases-ui-design S3` | Decision pending |
| TD-008 | First-row insert race | V2 | Theoretical; acceptable for V1 |

---

## PO instructions

1. Walk through each of the 13 AC items above. Mark `[✓]`, `[~]`, or `[✗]`.
2. For any item not marked `[✓]`:
   - `[~]` accepted_with_notes — describe the note inline (will land as tech debt in the report).
   - `[✗]` rejected — describe the issue inline; the orchestrator will route to the right re-entry point per the skill template's root-cause table.
3. After marking, return to me and I will compile the final `uat_report.json` + `uat_report.md` from your decisions, then advance to `/ases-devops S3` (if APPROVED) or surgical re-entry (if REJECTED).

**Verdict line (PO to fill):** _________ (APPROVED / CONDITIONAL / REJECTED)
**Signed:** Jayanth · 2026-06-29

---

## UI Track Supplemental Pass — 2026-07-01

> The 13 ACs above were accepted at the **API layer** on 2026-06-29.
> The S3 UI track (Dashboard + Sales Report) was completed after that UAT.
> This section covers the UI-specific acceptance items requiring PO eyes-on.

**UI test totals:** 10/10 jest passing (TC-161..TC-170) · TD-010 CLOSED

### UI-specific items for PO review

```
[✓] AC-041-UI (F-010): Dashboard page renders a table with one row per active (design, grade),
    all 8 columns correct. Empty state CTA shown when no data for selected date.
    How to verify:
      1. Open http://localhost:3000/dashboard
      2. Select today's date — verify design/grade rows appear with all 8 columns
      3. Select a future date or a date with no transactions — verify EmptyDashboardState
         CTA renders (not a blank/broken screen)
      4. While data loads, verify a loading skeleton is shown (not a blank screen)
    Jest coverage: TC-161 (render+values), TC-162 (empty state), TC-163 (loading state)
    Backend UAT 2026-06-29: AC-041 accepted at API level
```

```
[✓] AC-049-UI (F-011): Both Consolidation and Transaction sections render simultaneously
    on the Sales Report page — no toggle, no tab. Consolidation first.
    How to verify:
      1. Open http://localhost:3000/reports/sales
      2. Confirm BOTH Consolidation table AND Transaction table visible at the same time
      3. Consolidation is above Transaction — no tab / accordion needed
    Note: This AC was accepted_with_notes in backend UAT (UI layer was pending).
    It is now shipped via /ases-ui-scaffold S3 + /ases-dev T-065.
```

```
[✓] AC-050-UI (F-011): ReconciliationBadge shows "Reconciled ✓" (green) when
    consolidation sum == transactions sum; "Mismatch" (red) if they differ.
    How to verify:
      1. Sales Report page → any filter → ReconciliationBadge shows "Reconciled ✓"
      2. Badge includes aria-live="polite" for screen-reader accessibility
    Jest coverage: TC-164 (reconciled), TC-165 (mismatch state)
    Backend UAT 2026-06-29: AC-050 accepted at API level
```

```
[✓] AC-046-UI (F-011): Multi-select filter dropdowns work correctly.
    How to verify:
      1. Sales Report → Dealer multi-select → select 2 dealers → results show both
      2. Sales Report → Place multi-select → select a place string → filters applied
      3. "Clear filters" button invokes reset (EmptyReportState shows when no results)
    Note: TD-010 CLOSED — MultiSelectComboboxFallback (native <select> shim) ships
    as the Radix jsdom-incompatible alternative. Numeric IDs coerce correctly (TC-169).
    Jest coverage: TC-166 (clear button), TC-169 (numeric onChange), TC-170 (string onChange)
    Backend UAT 2026-06-29: AC-046 accepted at API level
```

```
[✓] AC-047-UI (F-011): ConsolidationTable footer shows "Total" row summing total_nos.
    How to verify:
      1. Sales Report → Consolidation section → scroll to footer row
      2. Footer shows "Total" label + sum of all total_nos values
      3. Empty state: "No matching sales." renders when rows=[] (not a blank screen)
    Jest coverage: TC-167 (sum footer), TC-168 (empty state)
    Backend UAT 2026-06-29: AC-047 accepted at API level
```

**TD-010 closure confirmation:**
```
[✓] TD-010 CLOSED — MultiSelectComboboxFallback replaces Radix Select/Popover
    for filter dropdowns. Numeric option values coerce correctly (TC-169 PASS).
    String values pass through unchanged (TC-170 PASS). 10/10 frontend tests green.
```

**UI Track Verdict line (PO to fill):** APPROVED
**Signed:** Jayanth · 2026-07-01
