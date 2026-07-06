# Critique — T-081 · domain/invoice.py · Sprint V2 · Iteration 1

**Verdict: ✅ CLEAN**  
**Date:** 2026-07-03  
**Iteration:** 1 / 5 max  
**Findings (blocking):** 0  
**Observations:** 1  
**All TCs pass:** TC-176..TC-184 (9/9)

---

## Decisions Read First

| Decision | Relevant to |
|---|---|
| DS-007 | Four-layer architecture — domain layer has no I/O or SQLAlchemy imports |
| DS-022 | unit_price=0 allowed (schema-level validation upstream, not domain) |
| DS-023 | generate_invoice_number deterministic format confirmed |

---

## Lens 1 — Spec

**PASS** · 1 observation (non-blocking)

### OBS-001 — `compute_invoice_status`: `<= 0` vs `== 0` (observation only)

**Location:** `backend/src/domain/invoice.py:28`

The plan spec says:
```
paid_sum=sum(paid_amounts); if paid_sum==0 → 'PENDING'
```

Implementation uses:
```python
if paid_sum <= 0:
    return "PENDING"
```

**Impact:** None. Negative `paid_sum` is unreachable at runtime — `PaymentCreate.amount` is validated `gt=0` at the schema layer, so `paid_sum` can only ever be `>= 0`. All three relevant test cases (TC-181, TC-182, TC-183) produce identical results with either `== 0` or `<= 0`.

**Fix required:** No. The `<= 0` guard is a defensively better implementation for the domain function's own isolation. Flagged as observation only.

---

## Lens 2 — Contract

**PASS** — No findings.

| Export | LLD match | Signature match |
|---|---|---|
| `compute_line_total` | ✓ | `(int, Decimal) → Decimal` |
| `compute_invoice_total` | ✓ | `(list[Decimal]) → Decimal` |
| `compute_invoice_status` | ✓ | `(Decimal, list[Decimal]) → Literal[...]` |
| `generate_invoice_number` | ✓ | `(date, int) → str` |

- No SQLAlchemy imports ✓  
- No HTTP imports ✓  
- No I/O ✓  
- `depends_on: []` respected ✓  
- `_TWO_PLACES = Decimal("0.01")` module-level constant — avoids repeated construction ✓

---

## Lens 3 — Test

**PASS** — All 9 test cases pass.

| TC | Function | Input | Expected | Result |
|---|---|---|---|---|
| TC-176 | compute_line_total | qty=10, price=150.00 | 1500.00 | ✓ |
| TC-177 | compute_line_total | qty=0, price=150.00 | ValueError | ✓ |
| TC-178 | compute_line_total | qty=5, price=-10.00 | ValueError | ✓ |
| TC-179 | compute_invoice_total | [100.00, 200.50, 50.25] | 350.75 | ✓ |
| TC-180 | compute_invoice_total | [] | ValueError | ✓ |
| TC-181 | compute_invoice_status | total=1000, paid=[] | PENDING | ✓ |
| TC-182 | compute_invoice_status | total=1000, paid=[400] | PARTIAL | ✓ |
| TC-183 | compute_invoice_status | total=1000, paid=[600,400] | PAID | ✓ |
| TC-184 | generate_invoice_number | date(2026,7,2), id=42 | INV-20260702-00042 | ✓ |

**Edge cases covered:** qty=0, negative price, empty list, exact-match payment sum.

---

## Lens 4 — Security

**PASS** — No findings.

- `compute_line_total`: guards `quantity <= 0` and `unit_price < 0` — correct boundary enforcement
- `unit_price = Decimal(0)` is intentionally valid per DS-022 (zero-price fallback for missing prices)
- No external calls, SQL, secrets, or I/O

---

## Lens 5 — Structural

**SKIPPED** — Pure 4-function domain file. No `graphify-out/graph.json` analysis needed.

---

## Success Criteria Check

| Criterion | Status |
|---|---|
| 4 functions exported | ✓ |
| compute_line_total raises ValueError on qty<=0 | ✓ |
| compute_line_total raises ValueError on price<0 | ✓ |
| compute_invoice_total raises ValueError on empty list | ✓ |
| All Decimal results quantized to 2dp | ✓ |
| generate_invoice_number deterministic | ✓ |

**Manual verification:** `compute_line_total(10, Decimal("150"))` → `Decimal('1500.00')`, `generate_invoice_number(date(2026,7,2), 42)` → `'INV-20260702-00042'` ✓

---

## Next Action

**CLEAN → tasks.json T-081 status=complete → next task per execution_order**

T-081 unblocks T-084 (InvoiceService). T-084 depends on `[T-079, T-080, T-081, T-082]` — check T-080 and T-082 status before proceeding.
