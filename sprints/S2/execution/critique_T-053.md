# Critique — T-053 Sales router (F-008 API)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/sales.py` (32 lines, 1 router + 2 endpoints)

## Decisions referenced (read first)
- **DS-007** — pure delegation per S1 router pattern ✓
- **DS-010** — bare `/sales` prefix; `/api/v1` added by main.py at mount time ✓

## Lens 1 — Spec

### Endpoints (LLD `files[11]`)
- `POST /sales → 201 SalesRead` via `service.save_sale(payload)` ✓
- `GET /sales → list[SalesRead]` with 4 query filters ✓

### Function signatures
- `create_sale(payload: SalesCreate, service: SalesService = Depends(get_sales_service)) -> SalesRead` ✓
- `list_sales(date_from?, date_to?, dealer_ids?: list[int], design_ids?: list[int], service) -> list[SalesRead]` ✓

### Multi-select query binding
- `dealer_ids: list[int] | None = Query(default=None)` — FastAPI natively binds repeated query params `?dealer_ids=1&dealer_ids=2` into a `list[int]`. Same for `design_ids`. ✓
- Plan.md `DoD: Multi-select filters work natively (FastAPI default)` ✓

### Router instance
- `router = APIRouter(prefix="/sales", tags=["sales"])` matches LLD ✓

### Delegation
- Both endpoints are one-liners forwarding to the service via keyword args ✓
- No transformation, no router-level catch (exception propagation via S1 global handlers)

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["router (APIRouter prefix='/sales', tags=['sales'])"]` ✓

### Expects
- `SalesService` + DI factory `get_sales_service` ✓
- `SalesCreate`, `SalesRead` from `schemas/transactions.py` ✓
- `date`, `APIRouter`, `Depends`, `Query`, `status` ✓

### Imports vs depends_on[]
- 3 in-project files (T-046 schemas, T-048 service, T-051 dependencies) all referenced
- 5 total imports, all used

## Lens 3 — Test

T-053 `test_case_refs = ["TC-066"]` — traced:

| TC | AC | Path |
|---|---|---|
| TC-066 | AC-033 POST /sales returns 201; ledger decreases per line | `status_code=201` decorator + `service.save_sale(payload)` → T-048's per-line `stock.apply_sale(Δ=−nos)` ✓ |

## Lens 4 — Security

- Pydantic validates `SalesCreate` at boundary
- FastAPI's `Query(default=None)` coerces query strings to typed values; invalid → 422
- Multi-select `list[int]` binding bounds individual values via `int` parsing; no SQL injection risk (service uses `.in_()` parameterized binding)
- No raw SQL, no secrets, no logging
- Per DS-005 V1 has no auth — open endpoint

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 3 in-project modules (T-046/048/051) — all complete
- Will be imported by T-056 main.py for mounting
- No circular imports
- Orphaned in live call graph until T-056 mounts — documented dependency

Not critique-blocking.

## Verdict

**CLEAN** — Sales router mirrors T-052's pattern with 4-filter `list_sales`. Pure delegation. TC-066 traced. Multi-select query parameters wired via FastAPI native list[int] binding.

→ Update `tasks.json` T-053 status to `complete`, advance context. Next: T-054 (adjustments — POST only, no list endpoint per LLD), then T-055 (designs router MODIFY).
