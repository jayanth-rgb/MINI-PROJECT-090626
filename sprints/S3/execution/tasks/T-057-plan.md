# T-057 — `presentation/schemas/dashboard.py` — DashboardRow

**Module:** M-004 · **Depends on:** — (Group A)

## Context anchor
First file in S3 dev. No prior in-sprint tasks. Reads from S3 LLD `files[0]` and `schema.json` (read-only reuse). Mirrors the Pydantic v2 + `from_attributes=True` pattern used by `presentation/schemas/master.py` (S1) and `presentation/schemas/transactions.py` (S2 T-046).

## Implementation logic

```python
# backend/src/presentation/schemas/dashboard.py
from pydantic import BaseModel, ConfigDict


class DashboardRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    opening: int
    inward: int
    outward: int
    adjust: int
    closing: int
```

## Constraints
- Pydantic v2 only (BaseModel + ConfigDict).
- `from_attributes=True` because T-061 (DashboardService) hydrates instances from SQLAlchemy `Row` mappings.
- Field order in the class matches the LLD's column order for predictable JSON layout.
- No validators. No methods. No business logic.

## Do not touch
- Any other file in the repo.

## Success criteria
- **Manual**: `python -c "from src.presentation.schemas.dashboard import DashboardRow; print(list(DashboardRow.model_fields))"` → 10 keys in declared order.
- **Automated**: T-061 integration tests (TC-115, TC-129) instantiate `DashboardRow` from query rows without raising.
- **DoD**: file exists; exactly one BaseModel; 10 typed fields; `ConfigDict(from_attributes=True)`; nothing else.

## Checkout
> *"DashboardRow schema created. 10 fields, from_attributes=True. Ready for DashboardService projection in T-061."*
