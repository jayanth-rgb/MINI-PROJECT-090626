# T-003 — Tests

No dedicated tests — exception hierarchy verified through downstream service tests.

## Manual

```powershell
backend/.venv/Scripts/python.exe -c "from src.domain.exceptions import NotFoundError; raise NotFoundError('Foo', 1)"
# → NotFoundError: Foo with id 1 not found
```

## Indirect coverage
- TC-017 — ConflictError on duplicate grade_code
- TC-027, TC-028 — NotFoundError on non-existent design_id / grade_id
