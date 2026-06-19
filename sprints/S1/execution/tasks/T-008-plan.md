# T-008 — Error Handlers

**Module:** M-007 · **Depends on:** T-003 · **TC refs:** indirect

## Implementation logic

```python
# backend/src/presentation/api/errors.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import NotFoundError, ConflictError, ValidationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def _validation(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"detail": "unique constraint violation"})
```

## Constraints
- DS-007: presentation layer; does not import infrastructure
- Response shape `{"detail": str}` — matches FastAPI conventions
- IntegrityError is the safety net when service layer pre-check is bypassed (rare race)

## Do not touch
Any other file.

## Success criteria
- **Manual:** Stub run `python -c "from fastapi import FastAPI; from src.presentation.api.errors import register_error_handlers; app = FastAPI(); register_error_handlers(app); print(len(app.exception_handlers))"` → 4+ (the 4 we added)
- **Automated:** Indirect — TC-034 (404), TC-035 (409 via ConflictError + IntegrityError safety net), TC-038 (409)
- **DoD:** register_error_handlers callable; 4 status codes mapped

## Checkout prompt
*"Error handlers wired — NotFoundError→404, ConflictError→409, ValidationError→422, IntegrityError→409."*
