from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.presentation.api.errors import register_error_handlers
from src.presentation.api.routers import (
    dealers,
    design_grade_map,
    designs,
    grades,
    staff,
    suppliers,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Jayanth Trading Tiles API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(suppliers.router, prefix="/api/v1")
    app.include_router(staff.router, prefix="/api/v1")
    app.include_router(dealers.router, prefix="/api/v1")
    app.include_router(grades.router, prefix="/api/v1")
    app.include_router(designs.router, prefix="/api/v1")
    app.include_router(design_grade_map.router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
