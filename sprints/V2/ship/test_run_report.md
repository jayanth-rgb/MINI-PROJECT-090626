# V2 · Test Run Report

**Sprint:** V2
**Executed:** 2026-07-06 (re-run after PO Option A adjudication)
**Runner:** pytest 8.3.4 (backend/.venv, testcontainers postgres:16)
**Command:** `pytest backend/tests/ --tb=short`

---

## Headline

| Bucket | Total | Passed | Failed | Errors |
|---|---|---|---|---|
| **V2 scope (47 cases)** | 47 | **47** | **0** | 0 |
| S1/S2/S3 regressions | 167 | **167** | 0 | 0 |
| **Full suite** | **214** | **214** | **0** | **0** |

Runtime: **182.09 s**.

- **V2 scope gate:** ✅ PASS
- **Regression gate:** ✅ PASS
- **Overall gate verdict:** **PASS**

---

## PO decision (2026-07-06) — Option A

**DS-025 stands.** V1 APIs require JWT authentication; DS-005 formally superseded (its V1 no-auth posture ended at V2 T-092). Remediation of the 69 pre-V2 regressions scoped to `backend/tests/` only — zero source-tree changes.

---

## Preflight fixes (from the initial 2026-07-05 run)

Still authoritative. All three unblock the DS-025 remediation from executing.

### PF-1 · `python-multipart` missing
- Added `python-multipart==0.0.20` to [backend/requirements.txt](backend/requirements.txt). Resolves 79 setup errors caused by `src.main` import failing (V2 auth router uses OAuth2 Form dep).

### PF-2 · `bcrypt` 5.0 incompatible with `passlib` 1.7.4
- Pinned `bcrypt==4.2.1` in [backend/requirements.txt](backend/requirements.txt). Passlib's backend-detection routine crashes on bcrypt 5.x's 72-byte check.

### PF-3 · `InvoiceRepository.get` missing `.unique()`
- [backend/src/infrastructure/db/repositories/pricing.py:69](backend/src/infrastructure/db/repositories/pricing.py#L69) — inserted `.unique()` before `.scalar_one_or_none()`. Two collection joinedloads (lines, payments) required it under SQLAlchemy 2.0.

---

## Regression remediation (PO Option A — DS-025)

### Root cause (confirmed)
[T-092 · DS-025](.ases/decisions.json) attaches mount-level `Depends(get_current_user)` to all 11 V1 routers in [backend/src/main.py:45-55](backend/src/main.py#L45-L55). Pre-V2 test suites were written against the DS-005 V1 open-endpoint contract and hit the new guard, receiving 401 instead of their expected 2xx/4xx.

### Changes applied — all in `backend/tests/`

#### 1. Auth fixtures in [backend/tests/conftest.py](backend/tests/conftest.py)

- Seeded `SECRET_KEY` at import time (mirroring the existing `DATABASE_URL` placeholder pattern).
- Precomputed `_DEFAULT_SUPERVISOR_PASSWORD_HASH` once at module load — bcrypt hashing is ~200 ms/call and running it per-test would balloon the suite; the constant is reused across every `client` fixture instantiation.
- **`client` fixture** now:
  - Seeds a `__test_default_supervisor__` `UserModel` row into `db_session`,
  - Mints an 8-hour HS256 JWT via `create_access_token`,
  - Attaches `Authorization: Bearer <token>` to `TestClient.headers`.
  - Result: every existing S1/S2/S3 `client.<verb>(...)` call now authenticates by default. **Zero body edits needed** across 43 legacy test files.
  - Per-request `headers={"Authorization": ...}` overrides still win — V2 role-based tests (TC-211 STAFF, TC-212 admin, etc.) supply their own tokens and are unaffected.
- **`unauthenticated_client` fixture** added — no default header. Used only by the three tests below that assert the guard itself.

#### 2. [backend/tests/system/test_system_st002_no_auth_required_v1.py](backend/tests/system/test_system_st002_no_auth_required_v1.py)
Contract inverted. Now consumes `unauthenticated_client` and asserts `status_code == 401` with `WWW-Authenticate: Bearer` (RFC 6750) across all 6 V1 master endpoints. Function renamed `test_st002_list_endpoints_require_auth`. Docstring updated to cite DS-025 supersession of DS-005.

#### 3. [backend/tests/system/test_system_st011_s3_endpoints_no_auth.py](backend/tests/system/test_system_st011_s3_endpoints_no_auth.py)
Four `assert 200 ==` assertions inverted to `assert 401 ==` (no header + bogus Bearer, on `/dashboard` and `/reports/sales`). Added a 5th positive-control assertion using the authenticated `client` fixture to confirm the guard is not blanket-blocking. Function renamed `test_st011_s3_endpoints_require_auth`.

#### 4. [backend/tests/integration/v2/test_api_main.py](backend/tests/integration/v2/test_api_main.py)
TC-213 (unauthenticated V1 → 401) was implicitly authenticated by the new default `client` fixture on the first re-run and failed with `assert 200 == 401`. Switched to `unauthenticated_client` to test the intended contract.

### Fix loop trace
- Attempt 1 — conftest + ST-002 + ST-011 → 213 passed, 1 failed (TC-213 wired to authenticated fixture).
- Attempt 2 — rewire TC-213 → 214 passed. Green.

Within the 3-attempt cap.

### Confirmation
Full backend/tests/ suite: **214 passed, 0 failed, 0 errors** in 182.09 s.

---

## V2 scope — 47 / 47 PASS

| Test file | TCs | Result |
|---|---|---|
| backend/tests/unit/domain/test_auth.py | TC-171…TC-175 | 5 passed |
| backend/tests/unit/domain/test_invoice.py | TC-176…TC-184 | 9 passed |
| backend/tests/unit/infrastructure/test_pdf_exporter.py | TC-198 | 1 passed |
| backend/tests/unit/infrastructure/test_excel_exporter.py | TC-199 | 1 passed |
| backend/tests/unit/application/services/test_report_export_service.py | TC-200 | 1 passed |
| backend/tests/integration/v2/test_auth.py | TC-185, 186, 190–194 | 7 passed |
| backend/tests/integration/v2/test_pricing.py | TC-187–189, 201–206 | 9 passed |
| backend/tests/integration/v2/test_inward_report.py | TC-195, 196, 197 | 3 passed |
| backend/tests/integration/v2/test_api_auth.py | TC-208, 209, 210 | 3 passed |
| backend/tests/integration/v2/test_api_users.py | TC-211, 212 | 2 passed |
| backend/tests/integration/v2/test_api_main.py | TC-213 | 1 passed |
| backend/tests/integration/v2/test_api_inward_report.py | TC-214 | 1 passed |
| backend/tests/integration/v2/test_api_report_export.py | TC-215, 216 | 2 passed |
| backend/tests/integration/v2/test_api_invoices.py | TC-217 | 1 passed |
| backend/tests/integration/v2/test_stock_first_row_race.py | TC-207 | 1 passed |
| **Total** | **47** | **47 passed** |

---

## Non-blocking warnings (unchanged from 2026-07-05)

- `src/presentation/api/routers/report_export.py:32,66` — `Query(regex=...)` deprecated; use `pattern=`. Cosmetic.
- `src/infrastructure/exporters/pdf_exporter.py:120` and `python-jose/jwt.py:311` — `datetime.utcnow()` deprecated in Python 3.12. Cosmetic.
- `backend/tests/conftest.py:102` — `SAWarning transaction already deassociated` on 7 DB-constraint-violation tests. Pre-existing rollback pattern.

---

## Gate verdict

**PASS.** All critical-priority tests green; V2 scope and pre-V2 regression suite both fully green against the DS-025 contract.

## Next step

`/ases-integration-test V2`
