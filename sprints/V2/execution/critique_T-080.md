# Critique — T-080 · repositories/pricing.py · Iteration 2

**Sprint:** V2 · **Verdict:** ✅ CLEAN · **Date:** 2026-07-04

---

## ADR Pass

Decisions checked: DS-007 (four-layer architecture), DS-012 (BaseRepository[T] pattern), DS-022 (effective_from pricing + unit_price snapshot), DS-023 (on-demand invoice creation). No findings are ADR tradeoffs.

---

## Lens 1 — Spec

| Check | Result |
|---|---|
| `get_active_price` — `is_active.is_(True) AND effective_from <= today ORDER BY effective_from DESC LIMIT 1` | ✓ |
| `list_all` — all rows (incl. inactive) ordered by design_id, grade_id, effective_from DESC | ✓ |
| `create_with_lines` — atomic (two flushes in one transaction); returns header with lines eager-loaded via `self.get()` | ✓ (I-001 resolved) |
| `get` — `joinedload(lines, payments)` | ✓ |
| `list` — JOIN `SalesHeaderModel.header_id` (confirmed correct PK); optional filters `is not None` guarded; `ORDER BY invoice_date DESC` | ✓ |
| `PaymentRepository.create` — explicit field unpacking | ✓ |

---

## Lens 2 — Contract

| Check | Result |
|---|---|
| Exports: PriceMasterRepository, InvoiceRepository, PaymentRepository | ✓ |
| All extend BaseRepository per DS-012 | ✓ |
| `self.session` matches BaseRepository.__init__ | ✓ |
| I-002: `invoice_id` parameter name vs `id_` in BaseRepository.get (LSP) | minor |
| I-003: untyped `data` in PaymentRepository.create | minor |
| I-004: `create_with_lines` declares `-> InvoiceHeaderModel` but returns `self.get()` typed `InvoiceHeaderModel \| None` | minor |

---

## Lens 3 — Test

| TC | Requirement | Result |
|---|---|---|
| TC-187 | get_active_price returns most-recent effective_from among active rows | ✓ |
| TC-188 | get_active_price returns None when only row is inactive | ✓ |
| TC-189 | create_with_lines returns header with lines eager-loaded; lines_count=1, line_total correct | ✓ `self.get(header.id)` uses `joinedload(lines, payments)` |

---

## Lens 4 — Security

All queries use SQLAlchemy ORM parameterised statements — no injection vectors ✓. `**line_dict` kwargs originate from InvoiceService-prepared dicts, not raw user input ✓. Explicit field unpacking in PaymentRepository.create ✓.

---

## Issues

### I-002 · contract · minor (persists from iteration 1)
**Line 60** — `InvoiceRepository.get(self, invoice_id: int)` names the parameter `invoice_id` instead of `id_`. Positional callers (including `self.get(header.id)` from create_with_lines) are unaffected. Keyword callers using `get(id_=X)` would receive TypeError.

**Fix:** Rename to `id_`; update WHERE to `InvoiceHeaderModel.id == id_`.

---

### I-003 · contract · minor (persists from iteration 1)
**Line 97** — `PaymentRepository.create(self, invoice_header_id: int, data)` — `data` is untyped. LLD specifies `data: PaymentCreate`. mypy/pyright treats `data` as Any.

**Fix:** `from src.presentation.schemas.pricing import PaymentCreate`; annotate `data: PaymentCreate`. Use `TYPE_CHECKING` guard if needed.

---

### I-004 · contract · minor (new — introduced by I-001 fix)
**Line 46** — `create_with_lines` declares `-> InvoiceHeaderModel` but returns `self.get(header.id)` which is typed `InvoiceHeaderModel | None`. mypy/pyright will flag: *"Incompatible return value type (got 'InvoiceHeaderModel | None', expected 'InvoiceHeaderModel')"*. Runtime-safe (post-flush get always finds the row) but a static type error.

**Fix:** `result = self.get(header.id); assert result is not None; return result`. Or `from typing import cast; return cast(InvoiceHeaderModel, self.get(header.id))`.

---

## DoD Verification

| Criterion | Status |
|---|---|
| 3 repositories exported | ✓ |
| All extend BaseRepository per DS-012 | ✓ |
| `get_active_price` ORDER BY effective_from DESC LIMIT 1 | ✓ |
| `create_with_lines` atomic (single flush block) | ✓ |
| TC-187, TC-188, TC-189 satisfied | ✓ |

---

## Verdict: CLEAN

Major I-001 (lazy-load inconsistency) is resolved — `create_with_lines` now delegates to `self.get(header.id)` which uses the correct joinedload path. All DoD criteria met. Three minor issues (I-002, I-003, I-004) documented for awareness.

**Next:** proceed to the next pending task in the V2 execution order.
