# T-051 — Add 4 new service factories to dependencies.py

**Module:** M-002 · **Depends on:** T-047, T-048, T-049, T-050 · **DS:** DS-007, DS-012

## Implementation logic

Append to the existing `dependencies.py` (after the 6 master factories):

```python
from src.application.services.inward_service import InwardService
from src.application.services.sales_service import SalesService
from src.application.services.adjustment_service import AdjustmentService
from src.application.services.design_grade_cb_service import DesignGradeCbService


def get_inward_service(db: Session = Depends(get_db)) -> InwardService:
    return InwardService(db)


def get_sales_service(db: Session = Depends(get_db)) -> SalesService:
    return SalesService(db)


def get_adjustment_service(db: Session = Depends(get_db)) -> AdjustmentService:
    return AdjustmentService(db)


def get_design_grade_cb_service(db: Session = Depends(get_db)) -> DesignGradeCbService:
    return DesignGradeCbService(db)
```

## Constraints
- DO NOT MODIFY the 6 existing master factories (get_supplier_service .. get_design_grade_map_service).
- Same `Session = Depends(get_db)` pattern as S1.

## Do not touch
The 6 S1 factories. Any other file.

## Success criteria
- **Manual:** `import` resolves all 10 factories.
- **Automated:** Router integration tests exercise indirectly.
- **DoD:** 10 factories total (6 + 4); existing untouched.

## Checkout prompt
*"Dependencies extended — 4 new service factories ready for routers."*
