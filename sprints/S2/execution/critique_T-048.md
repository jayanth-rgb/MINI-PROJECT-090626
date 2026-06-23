# Critique — T-048 SalesService (F-008)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/sales_service.py` (130 lines, 1 class, 2 methods + __init__)

## Decisions referenced (read first)
- **DS-002** — `apply_sale` holds SELECT FOR UPDATE inside the service transaction ✓
- **DS-007** — strict layering preserved ✓
- **DS-013** — `place = dealer.place` snapshot at save (AC-029) ✓

## Lens 1 — Spec

### Method roster (LLD `files[6]`)
- `save_sale(payload: SalesCreate) → SalesRead` ✓
- `list_sales(date_from, date_to, dealer_ids?, design_ids?) → list[SalesRead]` ✓

### Substitutions vs T-047 (per plan.md)
| T-047 | T-048 | Match |
|---|---|---|
| `purchase_date` | `sales_date` | ✓ |
| `supplier_id` / SupplierRepository | `dealer_id` / DealerRepository (AC-029 / DS-013) | ✓ |
| Single `entered_by_id` | TWO staff: `loading_staff_id` + `verified_by_id` (AC-030) | ✓ |
| `stock.apply_inward` (Δ=+nos) | `stock.apply_sale` (Δ=−nos) | ✓ |
| `list_inwards` 2 filters | `list_sales` 4 filters (+ dealer_ids, design_ids) | ✓ |

### AC checks enforced
- AC-028 / ERR-001 / ERR-002: date bounds (future + 7-day prior) ✓
- AC-029 / DS-013: dealer active + place snapshot ✓
- AC-030: BOTH staff fetched + checked active in a single loop ✓ (same staff for both roles permitted — no inequality check)
- AC-031 / ERR-005: (design, grade) pair must be in active map ✓
- AC-032: nos > 0 enforced by stripping + reject-empty pattern (mirrors AC-024)
- AC-033: ledger Δ=−nos via apply_sale; V1 does NOT block negative running_balance ✓

### `list_sales` query construction
- `select(SalesHeaderModel)` base
- `dealer_ids` → direct `dealer_id.in_(...)` filter on header
- **`design_ids` → relationship traversal**: `SalesHeaderModel.lines.any(SalesLineModel.design_id.in_(...))` since design lives on the line. SQLAlchemy 2.x relationship .any() emits an EXISTS subquery — efficient and parameterized.
- Order by `sales_date DESC, header_id DESC`
- `.unique()` collapses lazy='joined' row multiplication ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["SalesService"]` — class defined at module level ✓

### Expects
LLD `interfaces.expects` = `[SalesHeaderRepository, DealerRepository, StaffRepository, DesignGradeMapRepository, domain.stock.apply_sale, Pydantic schemas]`
- All present ✓
- Additional repos imported (not in LLD expects but required by plan.md flow): `TradingDesignRepository`, `GradeRepository` for AC-031 active checks on each line's design + grade individually. Same pattern as T-047 — consistent.

### Imports vs depends_on[]
- 5 depends_on files all imported correctly
- Extra: `SalesHeaderModel` + `SalesLineModel` from T-042 models — needed for `list_sales` query construction. Same controlled DS-007 touch as T-047, escalated by one extra import for the line-level design filter.

### Dead-import scan
- `NotFoundError` correctly NOT imported (learned from T-047 critique note); `.get()` raises it transitively without local reference ✓
- No unused imports

## Lens 3 — Test

All 6 TCs traced:

| TC | AC | Path |
|---|---|---|
| TC-058 | AC-028 future sales_date | `if payload.sales_date > today_` ✓ |
| TC-059 | AC-028 > 7-day prior | `if payload.sales_date < today_ - timedelta(days=7)` ✓ |
| TC-060 | AC-029 / DS-013 place snapshot | `"place": dealer.place` ✓ |
| TC-062 | AC-030 verified_by inactive | loop over (`loading_staff_id`, `verified_by_id`) raises if `not staff.is_active` ✓ |
| TC-063 | AC-031 inactive pair | `pair is None or not pair.is_active` ✓ |
| TC-065 | AC-033 Δ=−nos, running=prior−nos | `stock.apply_sale` (uses Δ=−nos in T-045) ✓ |

## Lens 4 — Security

- Pydantic validates upstream (gt=0 on FK IDs, min_length=1 on lines, etc.)
- ORM expression API only; no raw SQL
- `.in_(dealer_ids)` and `.in_(design_ids)` use parameterized bind values — no injection
- `.any(...)` emits EXISTS subquery — also parameterized
- DS-002 lock per-line inside the same session

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 5 upstream tasks (T-042, T-043, T-045, T-046, S1 master + exceptions) — all complete
- Will be imported by T-051 (DI dependencies) and T-053 (sales router)
- No circular imports
- `SalesHeaderModel.lines` relationship (T-042) exposes `.any()` for the design_ids filter — verified to work for SQLAlchemy 2.x relationship().

Not critique-blocking.

## Transparency notes (not findings)

1. **TradingDesignRepository + GradeRepository extra imports** — LLD `expects` lists 4 repos but plan.md's AC-031 pair-validity check requires individually fetching design + grade to verify each is `is_active`. Same pattern as T-047 — consistent treatment.
2. **`SalesLineModel` import** — added beyond T-047's pattern because `list_sales` `design_ids` filter traverses the line relationship via `.any()`. Required since design_id lives on the line in F-008 (per T-042 model).
3. **Carried over T-047 learnings**: no `NotFoundError` import; no redundant try/except.

## Verdict

**CLEAN** — SalesService mirrors T-047 structure with the documented sales-specific substitutions. All 6 TCs (TC-058/059/060/062/063/065) traced. AC-028..AC-033 invariants enforced. `list_sales` supports the 4-filter shape S3's Sales Report (M-005) will reuse.

→ Update `tasks.json` T-048 status to `complete`, advance context. Next: T-049 (AdjustmentService — single-design header, software_cb snapshot via closing_balance, ERR-012 no-active-grades check) or T-050 (DesignGradeCbService — DF-003 endpoint).
