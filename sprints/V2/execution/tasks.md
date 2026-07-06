# Sprint V2 — Task Plan

**26 backend tasks · 6 execution waves · No UI tasks (UI track separate)**

## Execution Waves

| Wave | Tasks | Parallel? |
|------|-------|-----------|
| 1 | T-067, T-068, T-069, T-076, T-079, T-081, T-082 | Yes — all independent |
| 2 | T-070, T-074, T-075, T-077, T-080, T-085, T-086 | Yes — each depends only on Wave 1 |
| 3 | T-071, T-083, T-084, T-087 | Yes — each depends on Wave 1+2 |
| 4 | T-089 | Single — depends on all Wave 3 services |
| 5 | T-072, T-073, T-078, T-088, T-090, T-091 | Yes — all router tasks depend on T-089 |
| 6 | T-092 | Single — depends on all Wave 5 routers |

---

## M-008 — Authentication & Authorization

| ID | File | Type | TCs | Status |
|----|------|------|-----|--------|
| T-067 | `backend/src/infrastructure/db/models/auth.py` | create | — | pending |
| T-068 | `backend/src/domain/auth.py` | create | TC-171..175 | pending |
| T-069 | `backend/src/presentation/schemas/auth.py` | create | — | pending |
| T-070 | `backend/src/infrastructure/db/repositories/auth.py` | create | TC-185, TC-186 | pending |
| T-071 | `backend/src/application/services/auth_service.py` | create | TC-190..194 | pending |
| T-072 | `backend/src/presentation/api/routers/auth.py` | create | TC-208..210 | pending |
| T-073 | `backend/src/presentation/api/routers/users.py` | create | TC-211, TC-212 | pending |
| T-074 | `backend/db/migrations/versions/0004_v2_auth_pricing_tables.py` | create | — | complete |
| T-075 | `backend/scripts/seed_default_user.py` | create | — | pending |
| T-089 | `backend/src/presentation/api/dependencies.py` | **modify** | — | pending |
| T-092 | `backend/src/main.py` | **modify** | TC-213 | pending |

## M-009 — Inward Report

| ID | File | Type | TCs | Status |
|----|------|------|-----|--------|
| T-076 | `backend/src/presentation/schemas/inward_report.py` | create | — | pending |
| T-077 | `backend/src/application/services/inward_report_service.py` | create | TC-195..197 | pending |
| T-078 | `backend/src/presentation/api/routers/inward_report.py` | create | TC-214 | pending |

## M-010 — Report Export

| ID | File | Type | TCs | Status |
|----|------|------|-----|--------|
| T-085 | `backend/src/infrastructure/exporters/pdf_exporter.py` | create | TC-198 | complete |
| T-086 | `backend/src/infrastructure/exporters/excel_exporter.py` | create | TC-199 | pending |
| T-087 | `backend/src/application/services/report_export_service.py` | create | TC-200 | pending |
| T-088 | `backend/src/presentation/api/routers/report_export.py` | create | TC-215, TC-216 | pending |

## M-011 — Pricing & Invoicing

| ID | File | Type | TCs | Status |
|----|------|------|-----|--------|
| T-079 | `backend/src/infrastructure/db/models/pricing.py` | create | — | pending |
| T-080 | `backend/src/infrastructure/db/repositories/pricing.py` | create | TC-187..189 | pending |
| T-081 | `backend/src/domain/invoice.py` | create | TC-176..184 | pending |
| T-082 | `backend/src/presentation/schemas/pricing.py` | create | — | pending |
| T-083 | `backend/src/application/services/pricing_service.py` | create | TC-201 | pending |
| T-084 | `backend/src/application/services/invoice_service.py` | create | TC-202..206 | pending |
| T-090 | `backend/src/presentation/api/routers/pricing.py` | create | — | pending |
| T-091 | `backend/src/presentation/api/routers/invoices.py` | create | TC-217 | pending |

---

## TC Coverage

- **47 TCs total** in test_cases.json (TC-171..TC-217)
- **46 TCs** mapped to tasks above
- **1 TC** (TC-207) handled at /ases-test-impl only — tests existing `backend/src/domain/stock.py` advisory lock (DS-020/DS-015); no new V2 dev task required

---

## Key Decisions Constraining Implementation

| DS | Rule |
|----|------|
| DS-007 | Four-layer architecture — routers → services → repositories; no shortcuts |
| DS-008 | Soft-delete only (is_active=false) — no hard DELETE |
| DS-012 | BaseRepository[T] pattern — UserRepository, PriceMasterRepository, InvoiceRepository, PaymentRepository all extend it |
| DS-013 | place is a snapshot column on transaction rows — InwardReportService reads it as-is (no re-join) |
| DS-017 | Shared filter predicate pattern — InwardReportService mirrors SalesReportService exactly |
| DS-018 | JWT HS256 via python-jose, 8h TTL, bcrypt via passlib — no refresh tokens |
| DS-019 | RBAC via role enum column (STAFF/VERIFIER/SUPERVISOR); require_supervisor guard on Depends |
| DS-021 | reportlab (PDF) + openpyxl (XLSX), StreamingResponse |
| DS-022 | Active price = effective_from <= invoice_date ORDER BY DESC LIMIT 1; snapshot unit_price on invoice_line |
| DS-023 | Invoices created on-demand (not auto-triggered); UNIQUE(sales_header_id) prevents double-invoicing |

---

## Next Step

No UI tasks → `TD-008 TC coverage complete` → begin with:

```
/ases-validate T-067 V2
```
