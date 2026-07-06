# Critique: T-079 — models/pricing.py · Iteration 2

**Sprint:** V2 · **Verdict:** ✅ CLEAN · **Issues remaining:** 0

## Summary

F-001 fix correctly applied. All 4 FK columns referencing S1/S2 BigInteger PKs now carry explicit `BigInteger` type in `mapped_column()`, matching PostgreSQL's FK type-equality requirement. All four lenses pass.

---

## Lens 1 — Spec · PASS

| Check | Result |
|---|---|
| 4 model classes present | ✓ |
| `PriceMasterModel` columns + UniqueConstraint + CHECK>=0 + lazy='joined' | ✓ |
| `InvoiceHeaderModel` columns + UNIQUE(invoice_number) + UNIQUE(sales_header_id) + status DEFAULT 'PENDING' | ✓ |
| `InvoiceLineModel` columns + UNIQUE(sales_line_id) + DS-022 plain Integer design_id/grade_id | ✓ |
| `PaymentModel` columns + CHECK(amount>0) + notes nullable | ✓ |
| All inherit Base + TimestampMixin | ✓ |
| DoD satisfied | ✓ |

---

## Lens 2 — Contract · PASS

**F-001 RESOLVED** — `BigInteger` imported; all 4 cross-S1/S2 FK columns updated:

| Column | Before Fix | After Fix | Referenced PK |
|---|---|---|---|
| `PriceMasterModel.design_id` | Integer (inferred) | `BigInteger` | `tbl_trading_design_master.design_id` BIGINT |
| `PriceMasterModel.grade_id` | Integer (inferred) | `BigInteger` | `tbl_grade_master.grade_id` BIGINT |
| `InvoiceHeaderModel.sales_header_id` | Integer (inferred) | `BigInteger` | `tbl_sales_header.header_id` BIGINT |
| `InvoiceLineModel.sales_line_id` | Integer (inferred) | `BigInteger` | `tbl_sales_line.line_id` BIGINT |

Internal FKs remain Integer (inferred): `invoice_header_id` on InvoiceLineModel and PaymentModel reference `InvoiceHeaderModel.id (Integer)` — correct.

`back_populates` wiring: `lines ↔ invoice_header` (InvoiceLineModel) and `payments ↔ invoice_header` (PaymentModel) — both sides declared. ✓

Exports match lld.json `interfaces.exports`. ✓

---

## Lens 3 — Test · PASS

No direct `test_case_refs`. Manual import check will pass. T-080 (TC-187..TC-189) covers model correctness at integration level.

---

## Lens 4 — Security · PASS

Pure ORM definitions. No raw SQL. Named constraints at DB level. DS-023 status CHECK deferred to migration T-074 per plan — documented, not a defect.

---

## Findings

*None.*

---

**Next:** T-079 status → `complete`. Continue execution order.
