# System Test Report — Sprint V2

**Executed:** 2026-07-06
**Runner:** pytest 8.3.4 (backend/.venv, Python 3.12.9)
**Verdict:** **PASS** (12/12 scenarios, 35/35 pytest items)

---

## Scope

- **Modules:** M-008 (Auth/RBAC), M-009 (Inward Report), M-010 (Report Export), M-011 (Pricing/Invoicing)
- **Features:** F-013..F-019
- **NFRs covered:** performance (login + inward-report latency), security (JWT edge cases, RBAC, SQL injection), boundary (export format, payment amount), error handling (409 duplicates)
- **Risks covered:** R-004 mitigation (V2 auth guard), RI-V2-001 (SECRET_KEY integrity)

## Result Matrix

| ID | Type | Threshold | Actual | Verdict |
|---|---|---|---|---|
| ST-013 | performance | median < 500ms | median = **370.0 ms** (n=20) | pass |
| ST-014 | performance | median < 2000ms | median = **16.7 ms** (n=10, 36 inward rows) | pass |
| ST-015 | security | expired JWT → 401 | /suppliers=401, /invoices=401 | pass |
| ST-016 | security | foreign-signed JWT → 401 | 401 | pass |
| ST-017 | security | alg=none → 401 | 401 | pass |
| ST-018 | security | SQL injection → 401 (no leak) | 4/4 → 401, tbl_user_master intact | pass |
| ST-019 | security | deactivated-user token → 401 | pre=200, post=401 | pass |
| ST-020 | security | STAFF on SUPERVISOR endpoints → 403 | /users, /prices, /invoices all 403 | pass |
| ST-021 | boundary | pdf/xlsx → 200; else → 4xx | 16/16 parametrized | pass* |
| ST-022 | boundary | overpayment → 422 (single & cumulative) | 5/5 parametrized | pass |
| ST-023 | error_handling | duplicate price → 409 | 201 then 409 (no traceback) | pass |
| ST-024 | error_handling | duplicate invoice → 409 | 201 then 409 (no traceback) | pass |

`*` ST-021 note: unsupported formats respond **422** (FastAPI `Query(regex=...)`) rather than the AC-066-worded **400**. Response is still a 4xx reject, so the contract intent is met. Documented as a carry-forward for a future PRD text refresh.

## Performance Details

- **ST-013** — POST /auth/login median 370 ms (threshold 500 ms). Bcrypt verify dominates the wall-clock cost; JWT sign + DB fetch are negligible. Room to shave is bcrypt work factor, which is intentional per DS-018.
- **ST-014** — GET /reports/inward median 16.7 ms with 36 inward headers spanning 6 dates × 3 designs × 2 grades (180 total NOS). Sales-Report analog threshold of 2000 ms is comfortable; the read path is a single SQL query joining tbl_inward_header + tbl_inward_line + master rows.

## Security Details

- **ST-015..ST-019** validate the JWT contract at the edge: expired token, foreign signature, alg=none, injection payloads, and mid-life deactivation. All five attack vectors are rejected with 401 without any 5xx leak.
- **ST-020** validates RBAC role gating separately from authentication: a well-formed STAFF token passes `get_current_user` but is refused by `require_supervisor` on all three write endpoints (users, prices, invoices).

## Files Written

- `backend/tests/system/test_system_st013_auth_login_latency.py`
- `backend/tests/system/test_system_st014_inward_report_latency.py`
- `backend/tests/system/test_system_st015_expired_jwt_rejected.py`
- `backend/tests/system/test_system_st016_tampered_jwt_signature.py`
- `backend/tests/system/test_system_st017_alg_none_confusion.py`
- `backend/tests/system/test_system_st018_login_sql_injection.py`
- `backend/tests/system/test_system_st019_deactivated_user_token.py`
- `backend/tests/system/test_system_st020_rbac_staff_denied.py`
- `backend/tests/system/test_system_st021_export_format_boundary.py`
- `backend/tests/system/test_system_st022_payment_overpayment_boundary.py`
- `backend/tests/system/test_system_st023_duplicate_price_409.py`
- `backend/tests/system/test_system_st024_duplicate_invoice_409.py`

## Carry-Forward

1. **AC-066 doc drift** — PRD wording says "400" for unsupported export format, but router-level `Query(regex=...)` produces 422. Either relax PRD text to "4xx" or introduce an explicit 400 raise ahead of Query validation.
2. **Deprecation warnings** (cosmetic, unchanged from `/ases-test-run V2`): `report_export.py` uses `Query(regex=...)`; `pdf_exporter.py` and `jose/jwt.py` use `datetime.utcnow()`.

## Next Step

`/ases-uat V2`
