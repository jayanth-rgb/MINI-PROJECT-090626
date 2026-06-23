# T-056 — main.py: mount 3 new routers

**Module:** M-002 · **Depends on:** T-052, T-053, T-054, T-055 · **DS:** DS-010

## Implementation logic

Modify the existing `create_app()`:

```python
# In the import block, add:
from src.presentation.api.routers import (
    dealers, design_grade_map, designs, grades, staff, suppliers,
    # NEW in S2:
    inward, sales, adjustments,
)

# In create_app(), after the existing include_router calls:
app.include_router(inward.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(adjustments.router, prefix="/api/v1")
# designs.router is already included from S1 — T-055's new /grades-with-cb route comes along.
```

## Constraints
- DO NOT modify CORS configuration.
- DO NOT modify `register_error_handlers` order (must still come before routers).
- DO NOT modify the existing 6 S1 router mounts.
- DO NOT modify `/health`.
- DS-010: all new routers under `/api/v1`.

## Do not touch
Any existing wiring. Any other file.

## Success criteria
- **Manual:** `uvicorn src.main:app --reload` starts; `/docs` lists 9 router groups (suppliers, staff, dealers, grades, designs, design-grade-map, inward, sales, adjustments).
- **Automated:** Integration tests in `test_inward_api.py`, `test_sales_api.py`, `test_adjustments_api.py`, `test_designs_grades_with_cb_api.py` all collect + run.
- **DoD:** 3 new include_router calls; existing wiring untouched.

## Checkout prompt
*"main.py — 3 new routers mounted under /api/v1; designs.py route in T-055 comes via existing mount."*
