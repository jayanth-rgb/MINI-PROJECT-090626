# T-066 — `main.py` MODIFY — mount 2 new routers

**Module:** M-002 · **Depends on:** T-064, T-065

## Context anchor
Final wiring task. Adds the 10th and 11th `include_router` calls to `create_app`. After this lands, the full S3 API surface is reachable. Existing `main.py` (verified at `/ases-analyze S3`):

```python
from src.presentation.api.routers import (
    adjustments, dealers, design_grade_map, designs, grades,
    inward, sales, staff, suppliers,
)
# ... 9 include_router calls ...
```

## Implementation logic

```python
# At the top — add `dashboard` and `sales_report` to the tuple-import (keep alphabetical):
from src.presentation.api.routers import (
    adjustments,
    dashboard,           # NEW
    dealers,
    design_grade_map,
    designs,
    grades,
    inward,
    sales,
    sales_report,        # NEW
    staff,
    suppliers,
)

# Inside create_app(), AFTER the existing 9 include_router calls (e.g. after `adjustments`):
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(sales_report.router, prefix="/api/v1")
```

## Constraints
- The tuple-import stays alphabetically sorted (S1/S2 convention).
- Both new mounts use `prefix="/api/v1"` (matches the 9 existing mounts).
- `/health` endpoint untouched.
- `register_error_handlers(app)` call untouched.
- `add_middleware(CORSMiddleware, ...)` call untouched.
- Mount order: append AFTER `adjustments` (or wherever the existing block ends) — order does not affect routing in FastAPI, but consistency with the existing pattern matters for `git diff` readability.

## Do not touch
- `register_error_handlers` block
- CORS middleware block
- `/health` endpoint
- Any of the 9 existing `include_router` calls
- Any other file

## Success criteria
- **Manual**: `uvicorn src.main:app --reload`; `curl http://localhost:8000/api/v1/dashboard?as_of_date=2026-06-30` returns 200 (assumes PG is up); `curl http://localhost:8000/api/v1/reports/sales` returns 200; `curl http://localhost:8000/health` returns `{"status":"ok"}`; all 9 existing endpoints still reachable.
- **Automated**: T-063's TC-159/TC-160 + T-064's 4 TCs + T-065's 5 TCs all hit `/api/v1/{dashboard, reports/sales}` — they break immediately if the mount is missing.
- **DoD**: `git diff backend/src/main.py` shows only 2 added names in the import tuple + 2 new `app.include_router(...)` lines; CORS/error_handlers/9-existing-mounts/health byte-identical.

## Checkout
> *"main.py mounts dashboard + sales_report routers under /api/v1. S3 API surface complete. Ready for /ases-critique."*
