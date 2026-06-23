# Critique — T-055 Designs router MODIFY (+ /grades-with-cb)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/designs.py` (71 lines, 6 routes total: 5 S1 preserved + 1 new)

## Decisions referenced (read first)
- **DS-007** — pure delegation; no business logic ✓
- **DS-010** — bare `/designs` prefix; `/api/v1` added by main.py ✓

## Lens 1 — Spec

### S1 routes preserved byte-identical
| # | Route | S1 body |
|---|---|---|
| 1 | `GET /` (list_designs) | unchanged ✓ |
| 2 | `POST /` (create_design) | unchanged ✓ |
| 3 | `PATCH /{design_id}` (update_design) | unchanged ✓ |
| 4 | `DELETE /{design_id}` (delete_design) | unchanged ✓ |
| 5 | `GET /{design_id}/grades` (list_grades_for_design) | unchanged ✓ |

Line-by-line diff: all 5 S1 route definitions are byte-identical to the original file. Only the import block has changed (additions, no removals or in-place edits to existing names).

### New route (S2)
```python
@router.get("/{design_id}/grades-with-cb", response_model=list[DesignGradeReadWithCb])
def list_grades_with_cb_for_design(
    design_id: int,
    stock_date: date = Query(...),
    service: DesignGradeCbService = Depends(get_design_grade_cb_service),
) -> list[DesignGradeReadWithCb]:
    return service.list_active_grades_with_cb(design_id, stock_date)
```
- Path `/grades-with-cb` distinct from S1's `/grades` — no FastAPI route conflict ✓
- `stock_date: date = Query(...)` — REQUIRED query param (FastAPI returns 422 if missing) ✓
- `response_model=list[DesignGradeReadWithCb]` strips extras per Pydantic v2 ✓
- Returns `[]` when no active grades; frontend converts to ERR-012 per LLD (NOT the API's job) ✓

### Imports
- `from datetime import date` (stdlib) ✓
- `DesignGradeCbService` added alphabetically (before _map_service) ✓
- `get_design_grade_cb_service` added into existing dependencies tuple (alphabetically) ✓
- `DesignGradeReadWithCb` from `schemas/transactions` (T-046) ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["router (existing + new route)"]` — `router` is module-level; the new GET endpoint registers with the existing `router` via decorator ✓

### Expects
- `DesignGradeCbService` + `get_design_grade_cb_service` (T-050 + T-051) ✓
- `DesignGradeReadWithCb` (T-046) ✓
- All S1 imports preserved (DesignService, DesignGradeMapService, get_design_service, get_design_grade_map_service, master schemas) ✓

### Imports vs depends_on[]
- 3 new imports correspond to T-046 / T-050 / T-051 outputs (all complete)
- All imports verified to exist on disk via earlier Glob — IDE diagnostic was stale-cache false positive (same pattern as T-051)
- No dead imports

## Lens 3 — Test

T-055 `test_case_refs = ["TC-071"]` — traced:

| TC | AC | Path |
|---|---|---|
| TC-071 | AC-036 200 + projection + exact body keys | `response_model=list[DesignGradeReadWithCb]` strips extras; service projects each row with {grade_id, grade_code, software_cb} ✓ |

## Lens 4 — Security

- Path param `design_id: int` validated by FastAPI's int coercion
- Required `stock_date: date` via `Query(...)` — FastAPI parses ISO-8601 dates; 422 on malformed
- DI factory provides per-request session
- No raw SQL, no secrets
- `NotFoundError` from inactive/missing design propagates via S1's global handler → 404

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 3 in-project modules (T-046/050/051) — all complete on disk
- 5 existing import edges preserved
- Will be imported by S1's main.py (T-056 doesn't re-mount this router — it stays mounted from S1)
- No circular imports

Not critique-blocking.

## Transparency notes (not findings)

1. **IDE stale-cache diagnostic** flagged `design_grade_cb_service` and `schemas/transactions` as missing at write time — false positive (same pattern as T-051). Both modules exist on disk; runtime imports resolve correctly.
2. **`get_design_grade_cb_service` added to existing tuple** — slight in-place modification of the existing dependencies import block. The 2 existing names (`get_design_grade_map_service`, `get_design_service`) remain in the tuple alongside the new entry; alphabetically sorted (cb < map < service).

## Verdict

**CLEAN** — 5 S1 route definitions preserved byte-identical; 1 new GET endpoint appended per LLD `files[13]`. TC-071 wired via `response_model=list[DesignGradeReadWithCb]`. Pure delegation per DS-007.

→ Update `tasks.json` T-055 status to `complete`, advance context. **Last task remaining: T-056 (main.py MODIFY)** — mounts 3 new routers (inward, sales, adjustments) under /api/v1. The designs router stays mounted from S1; T-055's new endpoint comes along for free.
