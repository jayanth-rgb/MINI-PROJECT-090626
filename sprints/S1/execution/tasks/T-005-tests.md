# T-005 — Tests

No dedicated unit tests. Generic class is exercised by all 6 service test files transitively.

## Manual

```powershell
backend/.venv/Scripts/python.exe -c "from src.infrastructure.db.repositories.base import BaseRepository; print(hasattr(BaseRepository, 'soft_delete'), hasattr(BaseRepository, 'delete'))"
# → True False
```

## Critical invariant (DS-008)
The absence of `delete()` is a sprint-wide invariant. `/ases-critique` should flag any attempt by services or routers to add it back.

## Indirect coverage
- T-010..T-015 service tests exercise list, get, create, update, soft_delete via real repositories
- TC-005, TC-010, TC-014, TC-023 verify is_active filter behaviour
