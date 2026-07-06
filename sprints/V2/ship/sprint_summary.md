# Sprint V2 — Sprint Summary

- **Sprint**: V2 (Version 2 — Auth, RBAC, Pricing/Invoicing, Inward Report, Report Export)
- **Closed on**: 2026-07-05
- **Phase transition**: `SPRINT_EXECUTION` → `SPRINT_SHIP`
- **Next step**: `/ases-test-impl V2`

## Sprint Goal
V2 backend delivery across **M-008 (auth)**, **M-009 (inward report)**, **M-010 (report export)**, and **M-011 (pricing/invoicing)**. Introduces JWT (HS256, 8h TTL) via `python-jose` + `passlib` (**DS-018**), three-role RBAC — STAFF / VERIFIER / SUPERVISOR (**DS-019**), effective-from pricing with snapshotted immutable `unit_price` (**DS-022**), on-demand invoicing with `UNIQUE(sales_header_id)` (**DS-023**), and reportlab/openpyxl exports (**DS-021**). Closes **TD-008** (first-row insert race) via **DS-020**, leveraging the DS-015 advisory-lock pattern already shipped in S2.

## Task Summary
| Metric | Value |
|---|---|
| Total backend tasks | 26 |
| Completed | 26 |
| Deferred | 0 |
| Escalated (unresolved) | 0 |
| Escalations resolved in-sprint | 2 (T-072 reinterpretation, T-073 PO Option A scope amendment) |
| Iteration count (max / avg) | 4 / 1.58 |
| Critique verdicts | 22 CLEAN on critiqued tasks; 4 tasks reached complete without recording a `critique_verdict` field |
| UI tasks | 0 (deferred to `/ases-ui-design V2`) |

### Iteration distribution
```
0 iter : T-088, T-089
1 iter : T-067, T-068, T-071, T-075, T-076, T-077, T-081, T-082, T-083, T-085, T-086, T-087, T-090, T-091
2 iter : T-069, T-074, T-078, T-079, T-080
3 iter : T-072, T-084, T-092
4 iter : T-073
```

## Completed Tasks (26)
- **T-067** UserModel ORM
- **T-068** `domain/auth.py` — bcrypt + JWT (DS-018)
- **T-069** Auth Pydantic schemas
- **T-070** UserRepository
- **T-071** AuthService (authenticate + user CRUD)
- **T-072** Auth router (`/auth/login`, `/auth/me`) — CLEAN iter3 (DS-024)
- **T-073** Users router (SUPERVISOR CRUD, soft-delete) — CLEAN iter4 (PO Option A)
- **T-074** Alembic migration 0004 (5 V2 tables)
- **T-075** `seed_default_user.py` (idempotent admin seed)
- **T-076** InwardReport schemas
- **T-077** InwardReportService (shared filter predicate)
- **T-078** `/reports/inward` router
- **T-079** Pricing ORM (Price/InvoiceHeader/InvoiceLine/Payment)
- **T-080** Pricing repositories
- **T-081** `domain/invoice.py` — line/total/status arithmetic + invoice_number
- **T-082** Pricing Pydantic schemas
- **T-083** PricingService (DS-008 soft-delete + DS-022)
- **T-084** InvoiceService (DS-022 + DS-023) — CLEAN iter3
- **T-085** PdfExporter (reportlab)
- **T-086** ExcelExporter (openpyxl)
- **T-087** ReportExportService
- **T-088** `/reports/{sales,inward}/export` router — CLEAN
- **T-089** `dependencies.py` MODIFY — oauth2_scheme + guards + 5 DI factories — CLEAN
- **T-090** `/prices` router (SUPERVISOR-guarded POST + PATCH)
- **T-091** `/invoices` router (create_from_sales + record_payment)
- **T-092** `main.py` MODIFY — 6 V2 mounts + global auth guard on all 11 V1 routers — CLEAN iter3 (DS-025)

## Escalations Resolved

### T-072 — RESOLVED by reinterpretation
- iter2 fix-agent flagged out-of-scope; PO directed "go with T-072".
- iter3 CLEAN: TC-208/209 body field re-read as **semantic** payload description (not JSON wire format). Authoritative wire format is `application/x-www-form-urlencoded` per DS-018 + RFC 6749 §4.3.2 (OAuth2 password grant at token endpoint).
- Router unchanged. Logged as **DS-024**.

### T-073 — RESOLVED by PO Option A (bounded scope amendment)
- iter3 6 findings around users.py DELETE explicit `Response(204)`, workaround comments, DS-008 soft-delete routing, and LLD divergence (users.py 4 → 5 endpoints; auth_service.py 5 → 7 methods).
- PO Option A (2026-07-05): T-073 `output_files[]` amended to include `auth_service.py` (for `get_user` + `deactivate_user` only). LLD amended.
- iter4 CLEAN.

## New Decisions
| ID | Topic | Source |
|---|---|---|
| **DS-024** | V2 auth login wire format is OAuth2 form-encoded (`application/x-www-form-urlencoded`) per DS-018 + RFC 6749 §4.3.2. TC-208/209 body is semantic; Phase 3 test-impl will encode via httpx `data=`. LLD line 236 (`data: LoginRequest`) is documentation drift. | T-072 iter3 critique |
| **DS-025** | V2 non-auth routers use route-level `Depends(get_current_user)` inside each router file, NOT mount-level `dependencies=[…]` on `include_router`. Behaviorally equivalent under FastAPI Depends dedup; TC-213 unaffected. Documented inline on main.py:64 + 68-69. | T-092 iter3 F-092-4 accepted-as-tradeoff |

## Tech Debt

### Closed
- **TD-008** — First-row insert race in `tbl_stock_ledger`. Closed by **DS-020** (V2 LLD stage). The `pg_advisory_xact_lock(design_id, grade_id)` mandated by DS-015 already handles the first-row case in `domain.stock._apply` (shipped in S2). V2 adds Phase 3 regression **TC-207** to lock the fix in.

### New in V2
- None.

### Carry-forward
- LLD line 236 (`data: LoginRequest` prose vs OAuth2PasswordRequestForm reality) — refresh at next LLD update per DS-024.
- LLD prose "mount-level auth dep" vs V2-as-built "route-level auth dep" — DS-025 is authoritative for V2; refresh LLD prose at next LLD update.

## Test Case Coverage
- Total V2 TCs: **47** (TC-171 … TC-217)
- Task-mapped: **46**
- Test-impl only: **1** (TC-207 — DS-020 first-row insert race regression against existing `domain/stock.py`)

## Test Cases to Verify in Phase 3
```
TC-171..TC-175 (auth domain — hashing, JWT encode/decode)
TC-176..TC-184 (invoice arithmetic)
TC-185..TC-189 (repositories: UserRepository, PriceMasterRepository, InvoiceRepository, PaymentRepository)
TC-190..TC-194 (AuthService)
TC-195..TC-197 (InwardReportService)
TC-198..TC-200 (Exporters — PDF/Excel/Service router)
TC-201        (PricingService)
TC-202..TC-206 (InvoiceService including record_payment + overpayment guard)
TC-207        (DS-020 first-row insert race — integration test only)
TC-208..TC-210 (auth router)
TC-211..TC-212 (users router)
TC-213        (auth-guard regression across all V1 routers)
TC-214        (inward-report router)
TC-215..TC-216 (report-export router)
TC-217        (invoices router)
```

## Next Sprint Inputs

**Carry-forward tasks**
- LLD refresh: line 236 (DS-024) + mount-level dep prose (DS-025).

**Known constraints**
- V2 backend ships without a frontend — UI shipped separately via `/ases-ui-design V2 → /ases-ui-review V2 → /ases-ui-scaffold V2`. JWT auth state storage (localStorage vs httpOnly cookie) is a deferred UI-track decision.
- Seeded admin credentials (`admin/admin123`) must be rotated on first login — seed script warns but does not enforce.
- No token revocation in V2 — deactivated user's existing JWT remains valid until 8h TTL; `get_current_user` re-reads `is_active` per request so subsequent calls fail immediately (DS-018).

**Suggested PRD updates**
- Under F-013 AC, clarify login wire format is `application/x-www-form-urlencoded` (DS-024).
- V3 candidate: batch invoice creation endpoint for un-invoiced sales (per DS-023 tradeoffs).
- V3 candidate: refresh-token flow if sessions beyond 8h become required.

**New risks**
- **RI-V2-001 (informational)**: SECRET_KEY handling — production must set a strong SECRET_KEY env var before enabling auth in a shared environment.
- **RI-V2-002 (informational)**: DS-022 zero-price fallback — invoices created before price configuration carry `unit_price=0` lines; supervisor must notice and re-invoice or PATCH prices. Consider surfacing warning in UAT.

## Phase 3 Entry State
- 26 backend tasks ready for `/ases-test-impl V2`.
- All 178 tests from S1+S2+S3 must remain green when re-run — global auth guard on 11 V1 routers (T-092 side_effects) will force test-side auth-header injection.
- UI track not yet initiated for V2.

## Files Written by This Command
- `sprints/V2/ship/sprint_summary.json`
- `sprints/V2/ship/sprint_summary.md`
- `.ases/decisions.json` — appended DS-024, DS-025
- `.ases/context.json` — phase → SPRINT_SHIP, sprint_history V2 entry, completed_steps `sprint_close:V2`

## Next Command
```
/ases-test-impl V2
```
