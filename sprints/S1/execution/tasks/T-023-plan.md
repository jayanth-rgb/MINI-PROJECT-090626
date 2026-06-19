# T-023 — FastAPI App Factory

**Module:** M-007 · **Depends on:** T-001, T-008, T-017..T-022 · **TC refs:** — · **AC:** indirectly all

## Implementation logic

```python
# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.presentation.api.errors import register_error_handlers
from src.presentation.api.routers import (
    suppliers, staff, dealers, grades, designs, design_grade_map,
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
```

## Constraints
- DS-010: all routers mounted under `/api/v1`
- DS-005: no auth middleware in V1
- /health is unversioned (operational endpoint)
- Errors registered BEFORE routers so handlers see all exceptions

## Do not touch
Any other file.

## Success criteria
- **Manual:** `uvicorn src.main:app --reload` starts; `curl http://localhost:8000/health` -> `{"status":"ok"}`; `/docs` shows all 6 master routers
- **Automated:** Implicit through router integration tests
- **DoD:** create_app + module-level app; 6 routers + /health; CORS configured

## Checkout prompt
*"FastAPI main.py — app factory, CORS, 6 routers under /api/v1, /health."*
