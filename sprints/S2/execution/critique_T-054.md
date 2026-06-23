# Critique — T-054 Adjustments router (F-009 API)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/adjustments.py` (15 lines, 1 router + 1 endpoint)

## Decisions referenced (read first)
- **DS-007** — pure delegation; no business logic in router ✓
- **DS-010** — bare `/adjustments` prefix; `/api/v1` added by main.py ✓

## Lens 1 — Spec

### Router + endpoint (LLD `files[12]`)
- `router = APIRouter(prefix="/adjustments", tags=["adjustments"])` ✓
- `POST /adjustments → 201 AdjustmentRead` via `service.save_adjustment(payload)` ✓
- **No GET endpoint** — S2 ACs don't require it; matches LLD ✓

### Function signature
- `create_adjustment(payload: AdjustmentCreate, service: AdjustmentService = Depends(get_adjustment_service)) -> AdjustmentRead` ✓

### Delegation
- One-line body: `return service.save_adjustment(payload)` ✓
- No try/except, no transformation, no logging ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["router (APIRouter prefix='/adjustments', tags=['adjustments'])"]` ✓

### Expects
- `AdjustmentService` + `get_adjustment_service` (T-049 + T-051) ✓
- `AdjustmentCreate`, `AdjustmentRead` (T-046) ✓
- `APIRouter`, `Depends`, `status` (fastapi) ✓

### Imports vs depends_on[]
- 4 imports total, all used. No `date`, no `Query` (POST-only, no query params)
- Dead-import check: clean

## Lens 3 — Test

T-054 `test_case_refs = ["TC-076", "TC-078"]` — both traced:

| TC | AC | Path |
|---|---|---|
| TC-076 | AC-039 POST 201 + ledger=physical_cb | `status_code=201` + `service.save_adjustment` → T-049's apply_adjustment ✓ |
| TC-078 | AC-040 ERR-012 → 422 | `ValidationError` from `service.save_adjustment` (no active grades) → global 422 ✓ |

## Lens 4 — Security

- Pydantic validates `AdjustmentCreate` at boundary (including `@model_validator` for stock_date ≤ entry_date — T-046)
- DI factory provides per-request session via `get_db`
- No raw SQL, no secrets
- No router-level error handling — all exceptions propagate to S1 global handlers

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 3 in-project modules (T-046/049/051) — all complete
- Will be imported by T-056 main.py
- No circular imports

Not critique-blocking.

## Verdict

**CLEAN** — Adjustments router is a 1-endpoint pure-delegation file. POST-only per LLD. TC-076 + TC-078 both wired correctly via exception propagation through S1's global error handlers.

→ Update `tasks.json` T-054 status to `complete`, advance context. Next: T-055 (designs router MODIFY — adds GET /designs/{id}/grades-with-cb endpoint, preserves S1's existing 4 endpoints).
