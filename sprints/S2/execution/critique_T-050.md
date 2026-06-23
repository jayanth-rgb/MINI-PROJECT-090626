# Critique — T-050 DesignGradeCbService (DF-003 contract)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/design_grade_cb_service.py` (40 lines, 1 class, 1 method + __init__)

## Decisions referenced (read first)
- **DS-007** — pure read-only application service composing 2 repos + 1 domain function ✓
- **DS-008** — soft-delete read semantics applied (inactive design → NotFoundError, not ValidationError) ✓

## Lens 1 — Spec

### Method (LLD `files[8]`)
- `list_active_grades_with_cb(design_id: int, stock_date: date) → list[DesignGradeReadWithCb]` ✓

### Flow vs plan.md
1. ✓ `design = design_repo.get(design_id)` — raises `NotFoundError` if row missing
2. ✓ `if not design.is_active: raise NotFoundError("TradingDesign", design_id)` — DS-008 read semantics (inactive == missing from user POV)
3. ✓ `rows = map_repo.list_active_by_design(design_id)` — JOIN filter on `grade.is_active` per T-006 S1 contract
4. ✓ List comprehension projecting each row into `DesignGradeReadWithCb(grade_id, grade_code=row.grade.grade_code, software_cb=closing_balance(...))`
5. ✓ Empty result returns `[]` — AC-040 / ERR-012 frontend-side trigger per plan.md note

### Behavioral choice — read-side vs write-side error semantics
- Write services (T-047/048/049) raise `ValidationError` (→ 422) for inactive masters
- T-050 raises `NotFoundError` (→ 404) for inactive design — read endpoints hide soft-deleted resources from clients
- LLD explicitly specifies "NotFoundError otherwise" — implementation matches ✓

### Read-time vs snapshot
- `software_cb` is computed at REQUEST time (not snapshotted) per AC-036 — used by the Adjustment form's grade-row pre-populator to show the user "what the system thinks the balance is as of stock_date"
- After the user submits the adjustment, T-049's `save_adjustment` re-snapshots software_cb via the same `stock.closing_balance` call at SAVE time — these may differ if the ledger changes between form load and submit

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["DesignGradeCbService"]` — class defined at module level ✓

### Expects
LLD `interfaces.expects` = `[DesignGradeMapRepository.list_active_by_design, TradingDesignRepository, domain.stock.closing_balance, DesignGradeReadWithCb schema]`
- All 4 present and used ✓
- `row.grade.grade_code` works because `DesignGradeMapModel.grade = relationship("GradeModel", lazy="joined")` exists in S1's `models/master.py` — verified
- `list_active_by_design` returns `list[DesignGradeMapModel]` with `.grade` pre-loaded (lazy='joined') — no N+1 risk

### Imports vs depends_on[]
- 3 depends_on files all imported correctly
- `NotFoundError` import IS used (line 25) — not a dead import this time
- Skipped plan.md's `ValidationError` import (plan.md imported but never used — lint-equivalent)
- No `select` / ORM model imports (no list method needed)

## Lens 3 — Test

T-050 `test_case_refs = ["TC-070"]` — traced:

| TC | AC | Path |
|---|---|---|
| TC-070 | AC-036 software_cb projection per active mapping | List comprehension with `software_cb=stock.closing_balance(...)` ✓ |

## Lens 4 — Security

- `design_id: int` and `stock_date: date` validated by FastAPI query-param coercion upstream (T-055 router will declare `Query(...)`)
- All DB access via SQLAlchemy expression API + lazy-joined relationship traversal
- No raw SQL, no secrets, no logging
- `NotFoundError` messages use validated int (design_id from path/query) — no injection

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 3 in-project modules: `domain/stock.py` (T-045), `infrastructure/db/repositories/master.py` (S1), `presentation/schemas/transactions.py` (T-046) — all complete
- Will be imported by T-051 (DI dependencies) and T-055 (designs router modify — adds GET /designs/{id}/grades-with-cb)
- No circular imports
- `DesignGradeMapModel.grade` relationship verified to exist in S1 — `r.grade.grade_code` access is safe

Not critique-blocking.

## Transparency notes (not findings)

1. **Read-side soft-delete semantics differ from write services** — Inactive design returns 404 (NotFoundError) per LLD spec. Documented in code comment. Different from T-047/048/049 which raise ValidationError (→ 422). Intentional asymmetry per DS-008.
2. **Skipped plan.md's `ValidationError` import** — plan.md imported but never used in the implementation. Dead-import discipline applied (carried T-047 learning).
3. **`software_cb` computed at request time** — not snapshotted by this service. T-049's save_adjustment re-snapshots at save time, so a value drift between form-load and form-submit is possible (the eventual ledger record will be based on save-time `closing_balance`). Plan.md and AC-036 design this intentionally.

## Verdict

**CLEAN** — DesignGradeCbService implements the DF-003 contract exactly per LLD. TC-070 traced. Read-side error semantics consistent with DS-008. No dead imports.

→ Update `tasks.json` T-050 status to `complete`, advance context. **Parallel-group-B closes** (4 services complete: T-047/048/049/050). Next: **T-051 dependencies.py wiring** — adds 4 new DI factories for the 4 services just landed.
