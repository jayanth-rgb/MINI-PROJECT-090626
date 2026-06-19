# T-008 — Tests

No dedicated test file; behavior verified by integration tests.

## Indirect coverage
| TC | Verifies |
|----|----------|
| TC-034 | 404 — DELETE /api/v1/suppliers/{id} where id missing |
| TC-035 | 409 — POST /api/v1/grades duplicate grade_code (ConflictError or IntegrityError) |
| TC-038 | 409 — POST /api/v1/design-grade-map duplicate pair |

## Manual

```powershell
backend/.venv/Scripts/python.exe -c "from fastapi import FastAPI; from src.presentation.api.errors import register_error_handlers; app = FastAPI(); register_error_handlers(app); print(len(app.exception_handlers))"
# → 4 (or 5 if you count FastAPI's default)
```
