# Critique — T-049 AdjustmentService (F-009)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/adjustment_service.py` (90 lines, 1 class, save_adjustment + __init__)

## Decisions referenced (read first)
- **DS-002** — `apply_adjustment` holds SELECT FOR UPDATE per-line inside the service transaction ✓
- **DS-007** — strict layering preserved (service composes 3 repos + 2 domain functions) ✓

## Lens 1 — Spec

### Method (LLD `files[7]`)
- `save_adjustment(payload: AdjustmentCreate) → AdjustmentRead` ✓
- Raises: ValidationError (stock_date > entry_date), NotFoundError (design — via .get()), ValidationError (ERR-012 no active grades) ✓
- No `list_adjustments` per LLD (consciously omitted from F-009) ✓

### Flow vs plan.md
1. ✓ Defense-in-depth `stock_date <= entry_date` (backstops Pydantic T-046 + DB CHECK T-044)
2. ✓ `design = design_repo.get(payload.design_id)` + `is_active` check
3. ✓ `active_pairs = map_repo.list_active_by_design(design_id)` — empty → ERR-012 ValidationError
4. ✓ `active_grade_ids` set computed; each line's grade_id verified ∈ set
5. ✓ Per-line `software_cb = stock.closing_balance(stock_date)` snapshot (AC-036)
6. ✓ `difference = physical_cb - software_cb` (signed, no abs() — AC-038)
7. ✓ `repo.create_with_lines(header, line_payloads)` with software_cb + physical_cb + difference per line
8. ✓ Per-line `stock.apply_adjustment(stock_date, difference, header_id, line_id)` — **txn_date = stock_date** per plan.md (software_cb was computed AS OF stock_date)
9. ✓ Zero-difference optimization: ledger write skipped; audit row in adjustment_line remains
10. ✓ Single `session.commit()` for atomicity
11. ✓ Return `AdjustmentRead.model_validate(header)`

### Defensive additions
- **`sorted(header.lines, key=lambda l: l.line_id)`** + **`zip(..., strict=True)`** — `header.lines` via `lazy='joined'` has no ORDER BY guarantee; sorting by line_id (assigned in insert order via autoincrement) ensures the `(grade_id, difference)` tuple pairs with the correct persisted line. `strict=True` raises ValueError on length mismatch (catches future regressions).
- These are defensive deviations from plan.md's raw `zip(line_diffs, header.lines)`. Same logical behavior under normal conditions; safer under SQLAlchemy ordering surprises.

### What's NOT in this service (intentional)
- **No date-bounds check** (no 7-day window for adjustments — only stock_date ≤ entry_date constraint)
- **No staff active check** for `entered_by_id` — LLD/AC-034..040 don't require it (consciously different from F-007/F-008)
- **No grade `is_active` per-line check** — `list_active_by_design` already JOINs through `grade.is_active` (per S1 T-006 contract); the `active_grade_ids` set guarantees both pair AND grade activity
- **No design re-fetch per line** — done once at the top (single-design header per AC-034)

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["AdjustmentService"]` — class defined at module level ✓

### Expects
LLD `interfaces.expects` = `[AdjustmentHeaderRepository, DesignGradeMapRepository.list_active_by_design, domain.stock.{closing_balance, apply_adjustment}, Pydantic schemas]`
- `AdjustmentHeaderRepository` ✓
- `DesignGradeMapRepository.list_active_by_design` ✓ (S1 T-006 method, JOIN with grade.is_active)
- `stock.closing_balance` + `stock.apply_adjustment` ✓
- `AdjustmentCreate` + `AdjustmentRead` ✓
- Additional: `TradingDesignRepository` for design active check — necessary but not in LLD expects (consistent with T-047/T-048 pattern of fetching the entity to check is_active beyond what the repo signature suggests)

### Imports vs depends_on[]
- 5 depends_on files all referenced via imports
- No unused imports (verified — Session, stock, ValidationError, 3 repos, 2 schemas all in use)
- NO `NotFoundError` import — `.get()` raises it transitively (T-047 learning carried)
- NO `select` / ORM model imports — no list method needed
- NO `date` / `timedelta` — no local date arithmetic

## Lens 3 — Test

All 3 TCs traced:

| TC | AC | Path |
|---|---|---|
| TC-074 | AC-038 signed difference | `difference = line.physical_cb - software_cb` ✓ (no abs()) |
| TC-075 | AC-039 ledger atomicity, running=prior+difference=physical | `stock.apply_adjustment(... difference ...)` via T-045 `_apply` ✓ |
| TC-077 | AC-040 ERR-012 reject if no active grades | `if not active_pairs: raise ValidationError(...)` ✓ |

## Lens 4 — Security

- Pydantic validates upstream (gt=0 on FK IDs, ge=0 on physical_cb, min_length=1 on lines, cross-field stock_date<=entry_date)
- Domain ValidationError uses string interpolation of VALIDATED ints — no injection vector
- All DB access via SQLAlchemy expression API; no raw SQL
- DS-002 lock per-line via `apply_adjustment` → `_apply` → `latest_for_design_grade(for_update=True)` (T-045/T-043)

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 5 upstream files (T-043, T-045, T-046, S1 master + exceptions) — all complete
- Will be imported by T-051 (DI dependencies) and T-054 (adjustments router)
- No circular imports
- Composes 2 domain functions (`closing_balance`, `apply_adjustment`) — both verified CLEAN in T-045

Not critique-blocking.

## Transparency notes (not findings)

1. **`sorted(..., key=lambda l: l.line_id)` + `zip(..., strict=True)`** added beyond plan.md's raw zip. Defensive against `lazy='joined'` ordering. Same behavior in practice; safer under future SQLAlchemy quirks.
2. **Zero-difference optimization** — skips ledger row when `difference == 0`; audit row in `adjustment_line` remains for traceability. Defensible: PRD AC-039 says "applies the difference to the ledger" — applying 0 is a no-op semantically. Plan.md documents this choice (line 84).
3. **No staff active check** — consciously omitted; F-009 AC-034..040 don't include this rule (only F-008 AC-030 does). The service signature matches LLD's `raises:` clause exactly (only Design NotFound + the 2 ValidationErrors).
4. **txn_date = stock_date** for ledger writes (not entry_date) per plan.md note: "software_cb was computed AS OF stock_date". This pairs the ledger event with the business date the user attested to.

## Verdict

**CLEAN** — AdjustmentService implements F-009 exactly per LLD: single-design header (AC-034), stock_date≤entry_date defense-in-depth (AC-035), ERR-012 active-grades check (AC-040), per-line software_cb snapshot via closing_balance (AC-036), signed difference (AC-038), per-line apply_adjustment with txn_date=stock_date (AC-039). All 3 TCs (TC-074/075/077) traced. DS-002/DS-007 honored.

→ Update `tasks.json` T-049 status to `complete`, advance context. Next: T-050 (DesignGradeCbService — DF-003 GET endpoint backing). After T-050 completes, parallel-group-B closes and T-051 (DI wiring) unblocks.
