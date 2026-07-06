# T-092 — MODIFY `main.py` — Mount V2 Routers + Auth-Gate V1 Routes

**Module:** M-008 · **Wave:** 6 (after all Wave 5 router tasks) · **Depends on:** T-072, T-073, T-078, T-088, T-089, T-090, T-091

## Context anchor

Final task of Sprint V2. Wires all V2 routers into the FastAPI app and retrofits all existing V1 router mounts with JWT auth dependency. After this task, ALL existing V1 endpoints require a valid JWT (TC-213 verifies). The auth login endpoint (`/auth/login`) stays open because the auth router is mounted WITHOUT a global dependency — its `/me` route handles its own dep at route level.

## Implementation logic

**Step 1: Read existing main.py** — identify all existing `app.include_router(...)` calls (11 total from S1/S2/S3).

**Step 2: Add new imports** (at top, after existing imports):
```python
from fastapi import Depends
from presentation.api.dependencies import get_current_user
from presentation.api.routers.auth import router as auth_router
from presentation.api.routers.users import router as users_router
from presentation.api.routers.report_export import router as report_export_router
from presentation.api.routers.inward_report import router as inward_report_router
from presentation.api.routers.pricing import router as pricing_router
from presentation.api.routers.invoices import router as invoices_router
```

**Step 3: Modify all EXISTING include_router calls** — add `dependencies=[Depends(get_current_user)]` to each:
```python
# Before (example):
app.include_router(some_v1_router)

# After:
app.include_router(some_v1_router, dependencies=[Depends(get_current_user)])
```

**Step 4: Append new V2 router mounts** (after all existing include_router calls):
```python
# Auth router — NO global dep (login must remain open)
app.include_router(auth_router)

# Export router BEFORE inward report (prefix collision prevention — see T-088)
app.include_router(report_export_router)
app.include_router(inward_report_router)

# Remaining V2 routers — route-level deps handle auth
app.include_router(users_router)
app.include_router(pricing_router)
app.include_router(invoices_router)
```

## Constraints

- **READ EXISTING FILE FIRST** — MODIFY, not create. Preserve all existing content (middleware, lifespan, CORS, health endpoint).
- `report_export_router` (prefix `/reports`) MUST be before `inward_report_router` (prefix `/reports/inward`). FastAPI matches in registration order; `/reports/inward/export` must not match the inward report router's `GET ""` first.
- `auth_router` MUST NOT have `dependencies=[Depends(get_current_user)]` at mount level — `/auth/login` must stay open.
- V2 routers (users, pricing, invoices, inward_report, report_export) do NOT need `dependencies=[Depends(get_current_user)]` at mount level — every route already has the dep at route level. Avoids double-execution.
- If any existing V1 router already has a `dependencies=[...]` kwarg, MERGE rather than replace (append `Depends(get_current_user)` to the existing list).
- If `Depends` is already imported in main.py, do not duplicate the import.

## Do not touch

- Any existing route handlers, middleware, lifespan events, or CORS configuration in main.py.
- Any other file.

## Success criteria

- **Manual**: `python -m uvicorn src.main:app --reload` — starts without ImportError. GET /docs shows all V2 routes.
- **Automated**: TC-213 (GET any existing V1 endpoint without Authorization header → 401)
- **DoD**: 6 V2 routers mounted. All 11 V1 include_router calls have get_current_user dep. Mount order correct (export before inward). App starts cleanly.

## Checkout

> *"main.py modified. 6 V2 routers mounted (auth without dep, then report_export, inward_report, users, pricing, invoices). All 11 V1 routers now require JWT auth. Prefix collision prevented. TC-213 covered. Sprint V2 task decomposition complete — begin /ases-validate T-067 V2."*
