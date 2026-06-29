# Critique — T-064 · `backend/src/presentation/api/routers/dashboard.py`

**Sprint:** S3 · **Module:** M-004 · **Iteration:** 1 · **Verdict:** **CLEAN**

## Summary
Pure-delegation GET /dashboard router. Implementation is byte-faithful to the plan, the LLD `files[3]` entry, and all 7 critical properties enumerated by the orchestrator. No findings.

## Decisions consulted (intersect M-004)

| ID | Relevance |
|---|---|
| **DS-016** | Ledger-corruption signaling. The router deliberately does NOT trap `AssertionError` from `DashboardService.list_as_of` — letting it bubble to a 500 is the design signal. Confirmed: no try/except in the file. |
| **DS-007** | Four-layer architecture. Presentation router routes through application service via `Depends(get_dashboard_service)`; never reaches infrastructure directly. Confirmed. |
| **DS-010** | `/api/v1` versioning. Router uses `prefix="/dashboard"`; `/api/v1` mount is owned by T-066 per the do_not_touch boundary. Confirmed. |

## Lens results

### Lens 1 — Spec ✓
Plan calls for `APIRouter(prefix='/dashboard', tags=['dashboard'])`, single GET `""` endpoint, required `Query(...)` `as_of_date: date`, `Depends(get_dashboard_service)`, `response_model=list[DashboardRow]`, single-return body. All present at lines 9, 12, 14, 15, 17. Function signature matches LLD `files[3].functions[0]` (`list_dashboard`).

### Lens 2 — Contract ✓
- **Exports:** `router` is an `APIRouter` instance with the prescribed prefix and tags — satisfies LLD `interfaces.exports`.
- **Imports vs `depends_on[]`:** all 3 imports are from declared dependencies and all are used:
  - `DashboardService` from `src.application.services.dashboard_service` — used as parameter type-hint.
  - `get_dashboard_service` from `src.presentation.api.dependencies` — used in `Depends(...)`.
  - `DashboardRow` from `src.presentation.schemas.dashboard` — used in `response_model=list[DashboardRow]` and return type.
- Downstream contracts verified: `get_dashboard_service` exists at `dependencies.py:59`; `DashboardService.list_as_of(as_of_date: date) -> list[DashboardRow]` matches at `dashboard_service.py:37`.

### Lens 3 — Test ✓
- **TC-117** (200 OK with rows): pure delegation returns service output; FastAPI serializes via `response_model`. Satisfied.
- **TC-130** (response sort order design_name ASC, grade_code ASC): order is established at the service layer (`rows.sort` in `dashboard_service.py:104`); response_model serialization preserves list order. Satisfied.
- **TC-131** (missing `as_of_date` → 422): `Query(...)` (Ellipsis) marks the param required — FastAPI default behavior delivers 422 with no manual code. Satisfied.
- **TC-132** (malformed date → 422): FastAPI's `date` type coercion rejects pre-handler; service is never invoked, matching the TC-132 expected behavior. Satisfied.

### Lens 4 — Security ✓
- No secrets. Input validation is type-driven (`date` Query) which is the correct surface for this endpoint.
- No injection vector: `as_of_date` is a parsed `datetime.date` by the time it reaches the service, which uses parameterized SQLAlchemy queries.
- No try/except hides errors.
- Absence of auth is policy-conformant per DS-005 (V1 no-auth), not a defect.

### Lens 5 — Structural ✓
`graphify-out/graph.json` not consulted (skipped per protocol). Manual reachability check: `router` is exported for T-066's `include_router`; `list_dashboard` is reachable via FastAPI route registration; all imported symbols are used. No orphans or dead imports.

## Critical properties checklist

| # | Property | Status |
|---|---|---|
| 1 | `APIRouter(prefix="/dashboard", tags=["dashboard"])` | line 9 ✓ |
| 2 | Single endpoint `GET ""` (combined `/dashboard`) | line 12 ✓ |
| 3 | `as_of_date: date = Query(...)` (required) | line 14 ✓ |
| 4 | `response_model=list[DashboardRow]` | line 12 ✓ |
| 5 | Single return statement (`return service.list_as_of(as_of_date)`) | line 17 ✓ |
| 6 | NO try/except (AssertionError bubbles to 500 per DS-016) | confirmed absent ✓ |
| 7 | `Depends(get_dashboard_service)` factory wiring | line 15 ✓ |

## Findings
None.

## Do-not-touch violations
None. Files listed in `do_not_touch[]` (`dashboard_service.py`, `dashboard.py` schema, `main.py`, other routers) were not modified.

## Next action
Proceed.
