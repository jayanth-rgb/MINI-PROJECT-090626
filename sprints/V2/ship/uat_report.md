# V2 · UAT Report
> Produced by `/ases-uat V2` · Reviewer: **Jayanth (PO)** · Reviewed: **2026-07-06**

## Headline

- **Verdict: `CONDITIONAL`**
- 21 AC items reviewed against PRD v2 (F-013 through F-019 + DS-020)
- 20 accepted · 1 accepted_with_notes · 0 rejected
- Backend suite: **214 / 214 PASS** · V2 scope 47/47 · regression 167/167 · integration IS-013..IS-018 6/6 · system ST-013..ST-024 12/12
- Next step: `/ases-devops V2`

## Condition

**AC-066** (F-016, unsupported export format → 400) accepted with notes. The router returns **422** (FastAPI `Query(regex=...)` validator), not the literal 400 named in the AC. The contract is fulfilled at 4xx — every unsupported format (`csv`, `xml`, `txt`, `json`, `<script>`, `''`) is rejected as a client error and no bypass exists (STR ST-021 = 16/16 parametrized cases green, TC-200 green). Filed as **TD-011** for next PRD update — either relax AC text to "4xx" or add an explicit 400 pre-check in the router before Query validation. Non-blocking for `/ases-devops V2`.

## AC Review Summary

| Feature | ACs | Accepted | Notes | Rejected |
|---|---|---|---|---|
| F-013 · User Authentication | AC-054, AC-055, AC-056 | 3 | 0 | 0 |
| F-014 · RBAC + User Mgmt | AC-057, AC-058, AC-059, AC-060 | 4 | 0 | 0 |
| F-015 · Inward Report | AC-061, AC-062, AC-063 | 3 | 0 | 0 |
| F-016 · Report Export | AC-064, AC-065, AC-066 | 2 | 1 | 0 |
| F-017 · Pricing | AC-067, AC-068 | 2 | 0 | 0 |
| F-018 · Invoicing | AC-069, AC-070, AC-071 | 3 | 0 | 0 |
| F-019 · Payment | AC-072, AC-073 | 2 | 0 | 0 |
| DS-020 · TD-008 closure | AC-074 | 1 | 0 | 0 |
| **Total** | **21** | **20** | **1** | **0** |

## Cross-cutting decisions

| Decision | Verdict | Evidence |
|---|---|---|
| DS-018 (JWT HS256 · 8h · no cache) | accepted | ST-015, ST-016, ST-017, ST-019 |
| DS-019 (RBAC STAFF/VERIFIER/SUPERVISOR) | accepted | ST-020, TC-211, TC-212 |
| DS-020 (advisory-lock first-row race) | accepted | TC-207 |
| DS-021 (reportlab + openpyxl exports) | accepted | TC-198, TC-199, TC-200, TC-215, TC-216, ST-021 |
| DS-022 (immutable unit_price snapshot; zero-price fallback) | accepted | TC-187, TC-188, TC-203; RI-V2-002 raised |
| DS-023 (on-demand invoicing, UNIQUE sales_header_id) | accepted | TC-217, ST-024 |
| DS-024 (login = form-urlencoded per RFC 6749) | accepted | TC-208, TC-209, IS-013 |
| DS-025 (V1 no-auth ended; global JWT guard) | accepted | 214/214 backend tests green under Option A rewrite; ST-002, ST-011, TC-213 |

## Performance & security headroom (from `system_test_report.json`)

- **ST-013** POST /auth/login median = **370.0 ms** (< 500 ms NFR) — bcrypt-bound, ~ 26 % headroom
- **ST-014** GET /reports/inward median = **16.7 ms** on 36 headers (< 2000 ms NFR) — ~ 120× headroom; reconciliation invariant verified on first call
- **ST-015..ST-020** every JWT attack vector rejected 401/403 (expired, tampered, alg=none, deactivated, RBAC)
- **ST-018** 4/4 SQL-injection payloads at login endpoint → 401 with no traceback leak, `tbl_user_master` row for real_admin unchanged after DROP TABLE attempt

## Tech debt observed

| ID | Severity | Target | Description |
|---|---|---|---|
| TD-011 | minor | next PRD update | AC-066 text says 400 but /reports/{sales,inward}/export unsupported-format response is 422 (FastAPI Query regex). Either relax AC text or add explicit 400 pre-check. Non-blocking. |
| TD-012 | minor | next LLD update | V2 LLD line 236 docs `data: LoginRequest` but actual signature is OAuth2PasswordRequestForm per DS-024. LLD prose vs main.py mount-level auth dep drift per DS-025. |
| RI-V2-001 | informational | production deploy | Strong SECRET_KEY env var required before enabling auth in shared / production. Scaffold defaults are dev-only. |
| RI-V2-002 | informational | UI supervisor visibility | DS-022 zero-price fallback — invoices created before price configuration carry unit_price=0 lines. Consider warning in UI. |
| TD-001 | minor | V2 UI-track | shadcn calendar.tsx classNames patch — carried forward from S3 UI scaffold. |
| CF-001 | minor | PO manual smoke | Long-lived PG bring-up + alembic upgrade + seed still pending. Testcontainers covered all V2 tests. Non-blocker. |

Zero new critical tech debt introduced by V2. TD-008 **CLOSED** via TC-207.

## Phase 3 test totals

| Bucket | Result |
|---|---|
| Backend pytest suite | **214 / 214 PASS** · 0 failed · 0 errors · 0 skipped · 182.09 s |
| V2 scope test cases (TC-171..TC-217) | **47 / 47 PASS** |
| Regression cases (S1+S2+S3) | **167 / 167 PASS** |
| Integration scenarios (IS-013..IS-018) | **6 / 6 PASS** |
| System test scenarios (ST-013..ST-024) | **12 / 12 PASS** (35 pytest items after parametrization) |
| Regressions | 0 |
| Preflight fixes applied in Phase 3 | 3 (python-multipart added; bcrypt 4.2.1 pin; InvoiceRepository.get `.unique()`) |
| Regression remediation | PO Option A rewrite (conftest default JWT fixture + ST-002 + ST-011 + TC-213). Zero src/ changes. |

## Notes

20 of 21 ACs accepted on first PO review. Only AC-066 carries an accepted_with_notes flag — documentation drift, not a behaviour bug (4xx contract fulfilled). All new tech debt is minor/informational and non-blocking. TD-008 CLOSED via TC-207 regression under DS-020 (advisory-lock pattern already live from S2 DS-015). V2 introduces the first authenticated shipping baseline for the product — DS-025 formally supersedes DS-005 with PO sign-off logged in `test_run_report.po_decision_2026_07_06`. Substantial perf and security headroom across all NFR probes.

## Next

**`/ases-devops V2`** — proceed to git commit + release ceremony.
Follow-up carry-forward: fold TD-011 (AC-066 text) and TD-012 (LLD drift) into the next PRD/LLD update; do not gate `/ases-devops` on them.
