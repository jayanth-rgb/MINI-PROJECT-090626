from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError


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
        return JSONResponse(
            status_code=409,
            content={"detail": "unique constraint violation"},
        )
