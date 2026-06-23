# Critique — T-046 Pydantic v2 schemas for transactions

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/schemas/transactions.py` (138 lines, 13 public schemas + 1 private `_OrmModel` helper)

## Decisions referenced (read first)
- **DS-010** — schemas consumed under /api/v1 ✓
- **DS-013** — `place` is server-derived (server snapshots from supplier/dealer at save); NOT in any Create schema ✓
- **DS-007** — presentation layer, no business logic — schemas declare shape and field-level constraints only ✓

## Lens 1 — Spec

### Schema roster (LLD `files[9].functions`)
| Family | Schema | Status |
|---|---|---|
| Inward | InwardLineCreate | ✓ design_id gt=0, grade_id gt=0, nos default=None ge=0 |
| Inward | InwardCreate | ✓ purchase_date, supplier_id gt=0, entered_by_id gt=0, lines min_length=1, no `place` |
| Inward | InwardLineRead | ✓ line_id, design_id, grade_id, nos with from_attributes=True |
| Inward | InwardRead | ✓ header_id, purchase_date, supplier_id, place, entered_by_id, created_at, lines |
| Sales | SalesLineCreate | ✓ mirror of InwardLineCreate |
| Sales | SalesCreate | ✓ sales_date, dealer_id, loading_staff_id, verified_by_id (all gt=0), lines min_length=1, no `place` |
| Sales | SalesLineRead / SalesRead | ✓ |
| Adjustment | AdjustmentLineCreate | ✓ grade_id gt=0, physical_cb ge=0, **no software_cb** (server-snapshotted per AC-036) |
| Adjustment | AdjustmentCreate | ✓ stock_date, entry_date, **design_id on header (AC-034)**, entered_by_id, lines min_length=1, + cross-field validator |
| Adjustment | AdjustmentLineRead | ✓ includes software_cb + difference (server-computed) |
| Adjustment | AdjustmentRead | ✓ |
| DF-003 | DesignGradeReadWithCb | ✓ {grade_id, grade_code, software_cb} |

### Cross-field validator (AC-035 / ERR-010)
```python
@model_validator(mode="after")
def _validate_dates(self) -> "AdjustmentCreate":
    if self.stock_date > self.entry_date:
        raise ValueError("stock_date must be on or before entry_date")
    return self
```
- `mode="after"` ensures all fields are typed before the check runs ✓
- Raises `ValueError` → Pydantic converts to `ValidationError` → FastAPI returns 422 ✓
- Backstopped at the DB level by `ck_adjustment_header_dates` (T-042 + T-044) — defense-in-depth ✓

### Field constraint registry
| Field | Constraint | AC ref |
|---|---|---|
| `*_id` (design, grade, supplier, dealer, staff) | `Field(gt=0)` | matches lld interfaces |
| `nos` on LineCreate | `Field(default=None, ge=0)` | RULE-017 skip semantics; service strips before final nos>0 check |
| `physical_cb` on AdjustmentLineCreate | `Field(ge=0)` | AC-037 (zero valid) — TC-073 |
| `lines` on all *Create | `Field(min_length=1)` | RULE-015 |
| `place` | absent from all *Create; present on *Read | DS-013 |

### `_OrmModel` private helper
- Leading underscore — not in LLD exports list (correctly internal)
- Bundles `ConfigDict(from_attributes=True)` so all 6 Read schemas inherit ORM compatibility
- 6 Read schemas correctly inherit `_OrmModel`; 7 Create schemas + DesignGradeReadWithCb inherit `BaseModel` directly

## Lens 2 — Contract

### Exports
LLD `interfaces.exports` lists 13 names — all 13 defined at module level ✓
`_OrmModel` correctly excluded (underscore-prefixed private)

### Expects (LLD declaration)
| Import | Use |
|---|---|
| `pydantic.BaseModel` | base class for all 14 schemas | ✓ |
| `pydantic.ConfigDict` | `_OrmModel.model_config` | ✓ |
| `pydantic.Field` | gt/ge/default/min_length constraints | ✓ |
| `pydantic.model_validator` | AdjustmentCreate cross-field check | ✓ |

### Imports vs depends_on[]
- `depends_on = []` (empty) — schemas are leaf-level, no project deps required
- Only stdlib (`datetime`, `typing`) + `pydantic` — no unused imports

## Lens 3 — Test

T-046 `test_case_refs = [TC-052, TC-061, TC-067, TC-068, TC-072, TC-073]` — all 6 traced:

| TC | Input | Expected | Wired via |
|---|---|---|---|
| TC-052 | `InwardLineCreate(nos=-1)` | ValidationError | `nos: Field(ge=0)` rejects -1 ✓ |
| TC-061 | `SalesCreate(...)` missing `loading_staff_id` | ValidationError | required field (no default) ✓ |
| TC-067 | Multi-design adjustment payload | impossible by schema shape | `design_id` lives on `AdjustmentCreate` only, not on `AdjustmentLineCreate` ✓ |
| TC-068 | `AdjustmentCreate(stock_date='2026-06-22', entry_date='2026-06-21', …)` | ValidationError | `_validate_dates` raises ✓ |
| TC-072 | `AdjustmentLineCreate(physical_cb=-1)` | ValidationError | `physical_cb: Field(ge=0)` rejects -1 ✓ |
| TC-073 | `AdjustmentLineCreate(grade_id=1, physical_cb=0)` | accepted (zero valid) | `ge=0` allows 0 ✓ |

## Lens 4 — Security

- All inputs validated by Pydantic field-level + model-level validators at the API boundary
- No raw SQL, no `eval`, no `exec`, no `os.environ`
- No secrets, no logging
- `@model_validator(mode="after")` raises `ValueError` → Pydantic converts to `ValidationError` → FastAPI returns 422 with safe detail message
- `gt=0` on all FK IDs prevents `id=0` or negative IDs from reaching the service/repository layer (defense-in-depth before the FK constraint at the DB)

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file is a leaf at this point — only imports stdlib + pydantic; will be imported by T-047/048/049/050 services, T-052/053/054 routers, T-055 designs router. Documented 2-step dependency.
- No circular imports: `domain/` does not import from `presentation/`; `infrastructure/` does not import from `presentation/`. Schemas are the boundary that the service layer consumes.
- All 14 class definitions (13 public + 1 private) are reachable when the module is imported.

Not critique-blocking.

## Transparency notes (not findings)

1. **`typing.Optional` + `typing.List` instead of `int | None` + `list[X]`** — Plan.md uses the older `typing` style; my impl follows verbatim. Functionally equivalent under Python 3.11; PEP 604 syntax would also work. Stylistic; no impact.
2. **`_OrmModel` private helper class** — Not in LLD exports list. Acceptable DRY abstraction internal to this module; refactoring the 6 Read schemas to repeat `model_config = ConfigDict(from_attributes=True)` inline would be uglier. Underscore prefix correctly signals internal use.
3. **Empty default `lines: List[XxxLineRead] = []` on Read schemas** — Pydantic v2 allows mutable defaults safely (instances get fresh lists). When hydrating from SQLAlchemy ORM via `from_attributes=True`, the `.lines` collection from the relationship populates this — the default only activates if the ORM has no lines (which T-042 cascade='all, delete-orphan' guarantees against in practice).

## Verdict

**CLEAN** — 13 Pydantic v2 schemas written exactly to spec. Field-level constraints, `min_length` requirements, cross-field validator, `ConfigDict(from_attributes=True)` Read-schema base, and `place`-server-derived (DS-013) all correctly applied. 6 TCs (TC-052/061/067/068/072/073) all wired.

→ Update `tasks.json` T-046 status to `complete`, advance context. Sprint S2 backend dev is now 6/16 done (T-041..T-046). Parallel-group B opens: T-047/048/049/050 services (all depend on T-045 + T-046 — both complete).
