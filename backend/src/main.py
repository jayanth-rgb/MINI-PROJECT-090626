from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.presentation.api.errors import register_error_handlers
from src.presentation.api.routers import (
    adjustments,
    dashboard,
    dealers,
    design_grade_map,
    designs,
    grades,
    inward,
    sales,
    sales_report,
    staff,
    suppliers,
)

# V2 router imports (T-092)
from src.presentation.api.dependencies import get_current_user
from src.presentation.api.routers.auth import router as auth_router
from src.presentation.api.routers.users import router as users_router
from src.presentation.api.routers.report_export import router as report_export_router
from src.presentation.api.routers.inward_report import router as inward_report_router
from src.presentation.api.routers.pricing import router as pricing_router
from src.presentation.api.routers.invoices import router as invoices_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Jayanth Trading Tiles API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    # V1 routers — all require a valid JWT (TC-213)
    app.include_router(suppliers.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(staff.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(dealers.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(grades.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(designs.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(design_grade_map.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(inward.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(sales.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(adjustments.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(dashboard.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
    app.include_router(sales_report.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

    # V2 routers (T-092)
    # auth_router: NO global dep — /auth/login must remain open (DS-018)
    app.include_router(auth_router, prefix="/api/v1")

    # report_export_router (prefix=/reports) MUST be before inward_report_router
    # (prefix=/reports/inward) to prevent /reports/inward/export being swallowed
    # by the inward router's empty-string path before the export router can handle it.
    # Route-level get_current_user dep is declared in each router — no double-execution.
    app.include_router(report_export_router, prefix="/api/v1")
    app.include_router(inward_report_router, prefix="/api/v1")

    # Remaining V2 routers — route-level deps (get_current_user / require_supervisor)
    # declared per route; no mount-level dep to avoid double-execution.
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(pricing_router, prefix="/api/v1")
    app.include_router(invoices_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
