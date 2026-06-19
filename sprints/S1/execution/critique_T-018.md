# Critique — T-018 Staff Router

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/staff.py` (41 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — pure delegation to `StaffService`
- **DS-008** soft delete — DELETE returns the deactivated `StaffRead`
- **DS-010** API versioning — `/staff` prefix; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[17]` parity: 4 routes (list/create/update/delete). `APIRouter(prefix="/staff", tags=["staff"])` ✓. Plan.md pseudo-code matches verbatim.

## Lens 2 — Contract
- T-016 → `get_staff_service` ✓
- T-011 (transitive) → `StaffService` type annotation ✓
- T-007 → `StaffCreate / StaffRead / StaffUpdate` ✓
- Exports `router` per LLD `interfaces.exports` ✓

## Lens 3 — Test
- `test_case_refs = []` for the router; service-layer coverage via TC-008/TC-010 already validated in T-011. DoD ("Same shape as suppliers router using Staff schemas and StaffService") is satisfied — identical structure to `suppliers.py` with `Staff*` substitutions. ✓

## Lens 4 — Security
- Path param `staff_id: int` auto-coerced + 422 on non-int ✓
- POST body bound to `StaffCreate` enforcing `staff_name: min_length=1` (AC-004) ✓
- `response_model=StaffRead` strips ORM extras ✓
- No auth — DS-005 V1 limitation ADR-tracked ✓

## Lens 5 — Structural
- Mounted in `main.py` (T-023): `app.include_router(staff.router, prefix="/api/v1")` ✓
- All 4 routes reachable ✓

## Verdict
**CLEAN** — mirror of suppliers router with Staff types; soft DELETE returns row; no scope creep.
