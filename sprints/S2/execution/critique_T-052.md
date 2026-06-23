# Critique — T-052 Inward router (F-007 API)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/inward.py` (26 lines, 1 router + 2 endpoints)

## Decisions referenced (read first)
- **DS-007** — router is pure delegation; no business logic ✓
- **DS-010** — `/api/v1` prefix added by main.py mount; router uses bare `/inward` ✓

## Lens 1 — Spec

### Endpoints (LLD `files[10]`)
- `POST /inward → 201 InwardRead` via `@router.post("", response_model=InwardRead, status_code=status.HTTP_201_CREATED)` ✓
- `GET /inward → list[InwardRead]` with `Query(default=None)` for date_from/date_to ✓

### Function signatures
- `create_inward(payload: InwardCreate, service: InwardService = Depends(get_inward_service)) -> InwardRead` ✓
- `list_inwards(date_from: date | None = Query(default=None), date_to: date | None = Query(default=None), service: InwardService = Depends(get_inward_service)) -> list[InwardRead]` ✓

### Router instance
- `router = APIRouter(prefix="/inward", tags=["inward"])` — matches LLD exports ✓

### Delegation
- `create_inward` → `service.save_inward(payload)` ✓ (one-liner body)
- `list_inwards` → `service.list_inwards(date_from=date_from, date_to=date_to)` ✓ (keyword forwarding)
- No try/except, no transformations, no logging — pure delegation per DS-007 ✓

### Exception propagation
- `ValidationError` (date bounds, no valid lines, inactive masters) → 422 via S1's `register_error_handlers`
- `NotFoundError` (missing supplier/staff/design/grade) → 404 via S1's global handler
- No router-level catching needed (S1 pattern from supplier/staff/dealer routers) ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["router (APIRouter prefix='/inward', tags=['inward'])"]` — `router` defined at module level ✓

### Expects
LLD `interfaces.expects` = `[InwardService via Depends, InwardCreate/Read]`
- `InwardService` imported (for type annotation) ✓
- `InwardCreate`, `InwardRead` imported ✓
- `get_inward_service` imported (DI factory from T-051) ✓
- `date` from datetime (Query param typing) ✓
- `APIRouter`, `Depends`, `Query`, `status` from fastapi ✓

### Imports vs depends_on[]
- `backend/src/application/services/inward_service.py` (T-047) ✓
- `backend/src/presentation/api/dependencies.py` (T-051) ✓
- `backend/src/presentation/schemas/transactions.py` (T-046) ✓
All 5 imports used. No dead imports.

## Lens 3 — Test

T-052 `test_case_refs = ["TC-048", "TC-057"]` — both traced:

| TC | Description | Wired via |
|---|---|---|
| TC-048 | POST /inward with future purchase_date → 422 | `ValidationError` from `service.save_inward()` → global handler returns 422 ✓ |
| TC-057 | POST /inward 201 + ledger increases per line | `service.save_inward(payload)` returns hydrated `InwardRead`; `status_code=201` decorator ✓ |

## Lens 4 — Security

- Pure delegation: no user input flows through router logic beyond Pydantic-validated `InwardCreate`
- DI factory `get_inward_service` provides a per-request session via `get_db` (S1)
- FastAPI auto-rejects malformed JSON / type mismatches with 422 via Pydantic
- No raw SQL, no logging, no secrets
- Per DS-005 V1 has no auth — endpoints are open (documented at V1 level)

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 3 in-project modules: `inward_service.py` (T-047), `dependencies.py` (T-051), `schemas/transactions.py` (T-046) — all complete
- Will be imported by T-056 main.py for `app.include_router(router, prefix="/api/v1")`
- No circular imports (router is a presentation leaf)
- Orphaned in live call graph until T-056 mounts it — documented dependency

Not critique-blocking.

## Verdict

**CLEAN** — Inward router is pure delegation per DS-007. 2 endpoints with correct status codes, response models, and dependency injection. Exception propagation handled by S1 global handlers (no router-level catches). TC-048 + TC-057 both traced. Matches LLD `files[10]` signatures verbatim.

→ Update `tasks.json` T-052 status to `complete`, advance context. Next: T-053 (sales router — mirror with 4-filter list_sales), then T-054 (adjustments — POST only), then T-055 (designs router MODIFY — adds /grades-with-cb).
