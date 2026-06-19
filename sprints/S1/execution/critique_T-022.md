# Critique — T-022 Design-Grade Map Router

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/design_grade_map.py` (49 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — router delegates fully; `ConflictError` / `NotFoundError` propagate unhandled
- **DS-008** soft delete — DELETE returns the deactivated `DesignGradeMapRead`
- **DS-010** API versioning — `/design-grade-map` prefix; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[21]` parity: 4 admin CRUD endpoints. `APIRouter(prefix="/design-grade-map", tags=["design-grade-map"])` ✓. Plan.md matches verbatim. Critically, the nested `GET /designs/{id}/grades` is NOT in this router (lives in T-021) per plan constraint ✓.

## Lens 2 — Contract
- T-016 → `get_design_grade_map_service` ✓
- T-015 (transitive) → `DesignGradeMapService` (raises `NotFoundError` for bad FK, `ConflictError` for duplicate pair) ✓
- T-007 → `DesignGradeMapCreate / DesignGradeMapRead / DesignGradeMapUpdate` ✓
- T-008 (transitive, error handler) → `ConflictError → 409`, `NotFoundError → 404` ✓
- Exports `router` per LLD `interfaces.exports` ✓

## Lens 3 — Test
- **TC-038** (AC-016, duplicate pair → 409): Router calls `service.create_mapping(payload)` without try/except. Service's `repo.get_by_pair` pre-check (T-015) raises `ConflictError("(design_id, grade_id) = (10, 1) already exists")`. T-008's global handler maps to HTTP 409 with body detail containing `"design_id, grade_id"` substring per expected_output. ✓
- Bad-FK paths (`NotFoundError` for missing design or grade) propagate as 404 — also testable from this endpoint though not in T-022's explicit TC list. ✓

## Lens 4 — Security
- Path param `map_id: int` auto-coerced + 422 on non-int ✓
- POST body bound to `DesignGradeMapCreate` enforcing `design_id: gt=0`, `grade_id: gt=0` — blocks negative or zero IDs at the boundary ✓
- Defense-in-depth on uniqueness: service pre-check (T-015) → DB `UNIQUE(design_id, grade_id)` (T-004) → `IntegrityError` handler (T-008) — race-safe ✓
- `response_model=DesignGradeMapRead` strips ORM extras (e.g. lazy-joined `design`/`grade` ORM objects beyond the projected `design_name` / `grade_code`) ✓
- No auth — DS-005 V1 limitation ADR-tracked ✓

## Lens 5 — Structural
- Mounted in `main.py` (T-023): `app.include_router(design_grade_map.router, prefix="/api/v1")` ✓
- All 4 routes reachable ✓
- Clean separation: read-projection endpoint lives in `designs.py` (T-021); admin CRUD lives here — no duplication ✓

## Verdict
**CLEAN** — 4-endpoint admin CRUD; TC-038 (duplicate pair → 409 + body detail substring `"design_id, grade_id"`) satisfied by exception propagation. Soft DELETE returns row per DS-008. Pydantic `gt=0` blocks invalid FK IDs before they reach the service.
