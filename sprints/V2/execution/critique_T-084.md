# Critique — T-084 `invoice_service.py` — Iteration 3

**Verdict: CLEAN** | Critical: 0 · Major: 0 · Minor: 0 | Issues remaining: 0

---

## Iteration Progress

| Iteration | Issues | Verdict |
|---|---|---|
| 1 | 1 critical + 1 major + 1 minor (3 total) | FIX_REQUIRED |
| 2 | 0 critical + 0 major + 1 minor (1 total) | FIX_REQUIRED |
| **3 (this run)** | **0 critical + 0 major + 0 minor** | **CLEAN** |

All four issues (I-001 through I-004) confirmed resolved.

---

## Lens 1 — Spec ✓

| Method | Requirement | Status |
|---|---|---|
| `create_from_sales` | 404 sales-header guard | ✓ lines 84–90 |
| | 409 duplicate-invoice guard (O(1) scalar) | ✓ lines 91–100 |
| | Fetch lines ORDER BY line_id | ✓ lines 102–105 |
| | Per-line price snapshot + zero-warning | ✓ lines 110–118 |
| | `compute_line_total` / `compute_invoice_total` | ✓ lines 119 / 131–133 |
| | `generate_invoice_number` | ✓ line 134 |
| | `create_with_lines` + commit + refresh | ✓ lines 143–145 |
| `list_invoices` | 4 optional filter params → InvoiceSummary list | ✓ lines 148–156 |
| `get_invoice` | 404 on None → InvoiceRead | ✓ lines 158–165 |
| `record_payment` | 404 + 422 overpayment guard | ✓ lines 167–183 |
| | `compute_invoice_status` recompute + header.status update | ✓ lines 184–186 |
| | commit + refresh → InvoiceRead | ✓ lines 187–189 |

`_to_invoice_read` assembles `InvoiceLineRead` via IN-query lookups on `TradingDesignModel` and `GradeModel`; `design_map` and `grade_map` keyed by IDs before list comprehension — no N+1 queries.

---

## Lens 2 — Contract ✓

All imports from `depends_on[]` used correctly:

- **T-079** `InvoiceHeaderModel`, `SalesHeaderModel`, `SalesLineModel` ✓
- **T-080** `InvoiceRepository`, `PaymentRepository`, `PriceMasterRepository` ✓
- **T-081** `compute_invoice_status`, `compute_invoice_total`, `compute_line_total`, `generate_invoice_number` ✓
- **T-082** `InvoiceLineRead`, `InvoiceRead`, `InvoiceSummary`, `PaymentCreate`, `PaymentRead` ✓

`InvoiceService` class exported at module level. DS-007 direct ORM access on `SalesHeaderModel`/`SalesLineModel` is accepted ADR trade-off (iteration-1 precedent, `ds007_direct_orm_access` critique note).

---

## Lens 3 — Test ✓

| TC | Scenario | Result |
|---|---|---|
| TC-202 | 2 lines (10×100.00 + 5×80.00) = 1400.00; line_0=100.00, line_1=80.00 | ✓ ORDER BY line_id ensures deterministic ordering |
| TC-203 | create_from_sales 409 when invoice already exists | ✓ scalar existence check lines 91–100 |
| TC-204 | unit_price snapshotted at creation; PATCH price master → invoice line unchanged | ✓ unit_price stored on InvoiceLineModel at creation |
| TC-205 | record_payment 500.00 → PAID status, 1 payment row | ✓ compute_invoice_status sum≥total → PAID |
| TC-206 | 400.00 existing + 200.00 new > 500.00 total → 422 | ✓ overpayment guard lines 175–182 |

---

## Lens 4 — Security ✓

- All DB queries use SQLAlchemy parameterization — no injection vectors
- `PaymentCreate.amount` validated by Pydantic schema (T-082: `gt=0`)
- `sales_header_id`, `invoice_id` typed as `int` at router boundary
- `HTTPException.detail` contains integer IDs only — no secrets, no PII
- No hardcoded credentials

---

## Lens 5 — Structural ✓

`InvoiceService` not yet wired into `main.py` — correct by DAG order (T-089 + T-091 are downstream pending tasks). All internal call edges present: `create_from_sales` → `_to_invoice_read`; `get_invoice` → `_to_invoice_read`; `record_payment` → `_to_invoice_read`. No dead imports.

---

## Resolved Issues Summary

| ID | Severity | Resolution |
|---|---|---|
| I-001 | critical | `_to_invoice_read` IN-query helper eliminates ValidationError; all 3 response paths use it |
| I-002 | major | O(1) scalar existence query replaces full-table `list` filter for duplicate check |
| I-003 | minor | `logger.warning` for zero-price lines; notes-column fix accepted as blocked on T-081/T-082 scope |
| I-004 | minor | `.order_by(SalesLineModel.line_id)` added (line 104) — TC-202 ordering deterministic |

---

## Reviewer Notes

**`record_payment` double-count verified safe:** `PaymentRepository.create` sets `invoice_header_id` as a FK column value only — no relationship attribute assignment. SQLAlchemy does not propagate FK-column-only assignments to already-loaded eager collections. `invoice.payments` on line 184 reflects only pre-existing payments; `data.amount` appended exactly once. No double-counting.

**DS-007 direct ORM access accepted:** `self._db.get(SalesHeaderModel, ...)` and `select(SalesLineModel)` bypass repository layer. `TransactionRepository` has no `get_by_pk` or `list_lines_by_header` interface in S2 scope. Iteration-1 precedent set. Accepted for T-084.

---

**T-084 status → complete. Next task in execution DAG.**
