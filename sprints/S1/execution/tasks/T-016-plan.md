# T-016 — FastAPI Dependency Providers

**Module:** M-001 · **Depends on:** T-002, T-010..T-015 · **TC refs:** — · **AC:** indirectly all

## Implementation logic

```python
# backend/src/presentation/api/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.db.session import get_db
from src.application.services.supplier_service import SupplierService
from src.application.services.staff_service import StaffService
from src.application.services.dealer_service import DealerService
from src.application.services.grade_service import GradeService
from src.application.services.design_service import DesignService
from src.application.services.design_grade_map_service import DesignGradeMapService


def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    return SupplierService(db)


def get_staff_service(db: Session = Depends(get_db)) -> StaffService:
    return StaffService(db)


def get_dealer_service(db: Session = Depends(get_db)) -> DealerService:
    return DealerService(db)


def get_grade_service(db: Session = Depends(get_db)) -> GradeService:
    return GradeService(db)


def get_design_service(db: Session = Depends(get_db)) -> DesignService:
    return DesignService(db)


def get_design_grade_map_service(db: Session = Depends(get_db)) -> DesignGradeMapService:
    return DesignGradeMapService(db)
```

## Constraints
- DS-007: presentation layer; only calls into application services
- No business logic — pure wiring

## Do not touch
Any other file.

## Success criteria
- **Manual:** `from src.presentation.api.dependencies import *` resolves all 6 names
- **Automated:** Exercised indirectly by TC-033..TC-038 router integration tests
- **DoD:** 6 callables, each takes a `Session = Depends(get_db)` argument

## Checkout prompt
*"API dependencies wired — 6 service factories ready for routers."*
