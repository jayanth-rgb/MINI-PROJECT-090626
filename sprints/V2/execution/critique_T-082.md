# Critique: T-082 — `schemas/pricing.py` — Pydantic v2 pricing + invoice schemas
**Sprint:** V2 | **Iteration:** 1 | **Verdict:** ✅ CLEAN

---

## Decisions read first
DS-007 (four-layer architecture), DS-018 (JWT auth), DS-019 (RBAC roles), DS-022 (unit_price snapshot), DS-023 (on-demand invoice creation). No ADR tradeoffs relevant to this schema file.

---

## Lens 1 — Spec

**Status: PASS**

All 8 schemas match the plan exactly.

| Schema | Fields | Validators | from_attributes |
|--------|--------|------------|-----------------|
| `PriceMasterCreate` | design_id, grade_id, unit_price, effective_from | `unit_price ge=0` ✓ | — |
| `PriceMasterRead` | id, design_id, design_name, size, grade_id, grade_code, unit_price, effective_from, is_active (9) | — | ✓ |
| `PriceMasterUpdate` | unit_price\|None, is_active\|None | — | — |
| `InvoiceLineRead` | id, sales_line_id, design_id, design_name, size, grade_id, grade_code, quantity, unit_price, line_total (10) | — | ✓ |
| `PaymentRead` | id, payment_date, amount, notes\|None (4) | — | ✓ |
| `PaymentCreate` | payment_date, amount, notes\|None | `amount gt=0` ✓ | — |
| `InvoiceRead` | id, invoice_number, sales_header_id, invoice_date, total_amount, status, lines, payments (8) | — | ✓ |
| `InvoiceSummary` | id, invoice_number, invoice_date, total_amount, status, sales_header_id (6) | — | ✓ |

**Definition of Done — fully met:**
- [x] 8 schemas exported
- [x] InvoiceRead, InvoiceLineRead, PaymentRead, PriceMasterRead have `from_attributes=True`
- [x] `PaymentCreate.amount` has `gt=0`
- [x] `PriceMasterCreate.unit_price` has `ge=0`
- [x] `len(InvoiceRead.model_fields) == 8`

---

## Lens 2 — Contract

**Status: PASS**

All 8 LLD exports present. Imports correct: `BaseModel`, `ConfigDict`, `Field` from pydantic; `Decimal` from decimal; `date` from datetime. `Field` is correctly imported despite being omitted from LLD `interfaces.expects` — it is required by the plan's validator specs (`ge=0`, `gt=0`). No project imports (correct — `depends_on: []`).

---

## Lens 3 — Test

**Status: PASS**

`T-082` carries `test_case_refs: []`. TC-201..TC-206 (assigned to T-083/T-084) consume these schemas as ORM-to-Pydantic serialization layers. Static compatibility verified:

- **TC-202**: `InvoiceRead.lines: list[InvoiceLineRead]` accepts 2 ORM lines; `unit_price: Decimal` serialises `"100.00"` / `"80.00"` correctly.
- **TC-205**: `InvoiceRead.status: str = "PAID"`; `payments: list[PaymentRead]` serialises payment amount.
- **TC-203 / TC-206**: Error paths (409, 422) — schemas not serialised; no schema-level interference.

---

## Lens 4 — Security

**Status: PASS**

Pure schema file — no I/O, no DB, no subprocess. Input validation is built-in: `unit_price ge=0` prevents negative price injection; `amount gt=0` prevents zero/negative payment bypass. No secrets or sensitive data handled.

---

## Lens 5 — Structural

**Status: SKIPPED** — 8 `BaseModel` subclasses with no call edges. Graph reachability analysis not applicable.

---

## Issues

*None.*

---

## Summary

| Metric | Value |
|--------|-------|
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Observations | 0 |
| Scope violation | No |
| Layer violation | No |
| Exports match LLD | Yes |

**Next:** `/ases-validate T-083 V2`
