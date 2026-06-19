# Critique — T-020 Grades Router

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/grades.py` (41 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — router delegates fully; `ConflictError` propagates unhandled
- **DS-008** soft delete — DELETE returns the deactivated `GradeRead`
- **DS-010** API versioning — `/grades` prefix; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[19]` parity: 4 routes (list/create/update/delete). `APIRouter(prefix="/grades", tags=["grades"])` ✓. Plan.md pseudo-code matches verbatim.

## Lens 2 — Contract
- T-016 → `get_grade_service` ✓
- T-013 (transitive) → `GradeService` (raises `ConflictError` on duplicate `grade_code`) ✓
- T-007 → `GradeCreate / GradeRead / GradeUpdate` ✓
- T-008 (transitive, error handler) → `ConflictError → 409` global mapping ✓
- Exports `router` per LLD `interfaces.exports` ✓

## Lens 3 — Test
- **TC-035** (AC-011, duplicate grade_code → 409): Router does NOT wrap `create_grade` in try/except — `ConflictError` raised by `GradeService.create_grade` (T-013 pre-checks via `repo.get_by_code` after strip; N-001 fix already resolved) propagates to FastAPI, where `register_error_handlers` (T-008) maps it to HTTP 409. The error body contains the service's message (which references `grade_code` — T-013 responsibility, already validated). ✓
  - Also robust to a race: if pre-check passes but a concurrent insert wins the UNIQUE constraint, `IntegrityError` is raised by SQLAlchemy and T-008's `IntegrityError → 409` handler catches it. ✓

## Lens 4 — Security
- Path param `grade_id: int` auto-coerced + 422 on non-int ✓
- POST body bound to `GradeCreate` (`grade_code: min_length=1`) ✓
- Defense-in-depth on uniqueness: service pre-check (T-013) → DB `UNIQUE(grade_code)` (T-004) → `IntegrityError` handler (T-008) ✓
- `response_model=GradeRead` strips ORM extras ✓
- No auth — DS-005 V1 limitation ADR-tracked ✓

## Lens 5 — Structural
- Mounted in `main.py` (T-023): `app.include_router(grades.router, prefix="/api/v1")` ✓
- All 4 routes reachable ✓

## Verdict
**CLEAN** — 4-endpoint shape; soft DELETE returns row; TC-035 satisfied by clean exception propagation through T-008's global handlers. No router-level catching of `ConflictError` — correct.
