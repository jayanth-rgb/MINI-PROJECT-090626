# T-063 — `presentation/api/dependencies.py` MODIFY — 2 new DI factories

**Module:** M-002 · **Depends on:** T-061, T-062

## Context anchor
Group C — a serial gate. Adds the 11th and 12th DI factories to the file. Existing pattern (S1+S2):

```python
def get_<noun>_service(db: Session = Depends(get_db)) -> <Noun>Service:
    return <Noun>Service(db)
```

Existing file has 10 factories (verified at `/ases-analyze S3`): supplier, staff, dealer, grade, design, design_grade_map, inward, sales, adjustment, design_grade_cb.

## Implementation logic

```python
# At the top of the existing import block, add:
from src.application.services.dashboard_service import DashboardService
from src.application.services.sales_report_service import SalesReportService

# At the end of the file, append:

def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_sales_report_service(db: Session = Depends(get_db)) -> SalesReportService:
    return SalesReportService(db)
```

## Constraints
- Two-line append-only edit to the import block + two new factory functions at the bottom.
- Imports stay alphabetically sorted within the existing `src.application.services.*` block.
- Existing 10 factories must be byte-identical (`git diff` should show only additions, no modifications).

## Do not touch
- Any existing factory function (`get_supplier_service`, `get_staff_service`, …, `get_design_grade_cb_service`).
- Any other file in the repo.

## Success criteria
- **Manual**: `from src.presentation.api.dependencies import get_dashboard_service, get_sales_report_service` succeeds; both callable with a session yield service instances of the right type.
- **Automated**: TC-159 + TC-160 pass — both routers (mounted in T-066) resolve their service dependencies correctly.
- **DoD**: `git diff` is purely additive (2 imports + 2 functions); no existing line altered.

## Checkout
> *"get_dashboard_service + get_sales_report_service appended. DI wired for T-064 + T-065 router mounts."*
