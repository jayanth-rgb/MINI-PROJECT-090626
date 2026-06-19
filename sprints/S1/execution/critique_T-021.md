# Critique — T-021 Designs Router (CRUD + DF-006 contract)

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/designs.py` (58 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — both `DesignService` and `DesignGradeMapService` consumed via Depends; no direct ORM
- **DS-008** soft delete — DELETE returns the deactivated `DesignRead`
- **DS-010** API versioning — `/designs` prefix; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[20]` parity: 5 endpoints — 4 CRUD on `/designs` plus nested `GET /{design_id}/grades`. ✓
- `list_designs`, `create_design`, `update_design`, `delete_design` — match `DesignService` methods
- `list_grades_for_design(design_id)` — uses `get_design_grade_map_service` (NOT `get_design_service`) per plan constraint ✓ (critical wiring detail correct)

`APIRouter(prefix="/designs", tags=["designs"])` ✓.

## Lens 2 — Contract
- T-016 → `get_design_service`, `get_design_grade_map_service` ✓
- T-014/T-015 (transitive) → `DesignService`, `DesignGradeMapService` type annotations ✓
- T-007 → `DesignCreate / DesignRead / DesignUpdate / DesignGradeReadMin` ✓
- Exports `router` per LLD `interfaces.exports` ✓

## Lens 3 — Test
- **TC-036** (AC-019, active projection): `GET /api/v1/designs/10/grades` with seed (design 10, grades 1/2, mappings (10,1) and (10,2) both active) → service returns `list[DesignGradeReadMin]` from `repo.list_active_by_design` (filters both `map.is_active` and `grade.is_active`). `response_model=list[DesignGradeReadMin]` guarantees body is exactly `[{grade_id, grade_code}, ...]` — no extra fields per AC-019 contract. ✓
- **TC-037** (AC-019, empty): `GET /api/v1/designs/20/grades` with no mappings → `repo.list_active_by_design(20)` returns `[]` → service returns `[]` → response body `[]` with status 200 (NOT 404). This is the ERR-012 path S2's Adjustment form depends on (HLD AC-040). ✓

## Lens 4 — Security
- Path param `design_id: int` auto-coerced by FastAPI; 422 on non-int ✓
- POST body bound to `DesignCreate` (`size: min_length=1`, `design_name: min_length=1` per AC-013) ✓
- `response_model=list[DesignGradeReadMin]` strips any extra ORM attributes from the join — prevents accidental leak of `design.is_active`, `map_id`, etc. ✓
- No auth — DS-005 V1 limitation ADR-tracked ✓

## Lens 5 — Structural
- Mounted in `main.py` (T-023): `app.include_router(designs.router, prefix="/api/v1")` ✓
- All 5 routes reachable; OpenAPI lists 4 CRUD + nested grades ✓
- Nested endpoint uses the correct service (verified at line 55) — common foot-gun avoided ✓

## Verdict
**CLEAN** — 5 endpoints; CRUD + DF-006 contract delivered. The nested `GET /{design_id}/grades` correctly wires `DesignGradeMapService` (not `DesignService`) and uses `list[DesignGradeReadMin]` as response_model to enforce the minimal projection per AC-019. Both critical TCs (TC-036, TC-037) satisfied.
