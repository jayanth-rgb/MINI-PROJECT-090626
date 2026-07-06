# T-089 — MODIFY `presentation/api/dependencies.py` — Auth guards + V2 DI factories

**Module:** M-008 · **Wave:** 4 (after all Wave 3 services) · **Depends on:** T-071, T-077, T-083, T-084, T-087

## Context anchor

Central DI wiring file. Existing content (get_db, V1 service factories) must be preserved exactly — READ THE FILE FIRST. V2 adds: JWT-based auth guards (oauth2_scheme, get_current_user, require_supervisor) and 5 new service DI factories. All Wave 5 router tasks depend on these additions.

## Implementation logic

```python
# APPEND to end of backend/src/presentation/api/dependencies.py
# (Read existing file first — do NOT overwrite; only append)

# These imports may already exist — check before adding:
# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordBearer

from domain.auth import decode_access_token
from infrastructure.db.repositories.auth import UserRepository
from application.services.auth_service import AuthService
from application.services.inward_report_service import InwardReportService
from application.services.pricing_service import PricingService
from application.services.invoice_service import InvoiceService
from application.services.report_export_service import ReportExportService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UserRepository(db).get_by_username(username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_supervisor(
    current_user=Depends(get_current_user),
):
    if current_user.role != "SUPERVISOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUPERVISOR role required",
        )
    return current_user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_inward_report_service(db: Session = Depends(get_db)) -> InwardReportService:
    return InwardReportService(db)


def get_pricing_service(db: Session = Depends(get_db)) -> PricingService:
    return PricingService(db)


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


def get_report_export_service(db: Session = Depends(get_db)) -> ReportExportService:
    return ReportExportService(db)
```

## Constraints

- **READ EXISTING FILE FIRST** — append-only. Never overwrite.
- `get_current_user` re-fetches `is_active` from DB on every call (DS-018 — token payload alone is not trusted for account status).
- `decode_access_token` returns `None` on any error (T-068 guarantees this). The 401 is raised here, not in domain layer.
- `require_supervisor` chains `Depends(get_current_user)` — FastAPI deduplicates the dep within a single request so get_current_user runs only once.
- `WWW-Authenticate: Bearer` header on all 401 responses (RFC 6750).
- Role string literal `"SUPERVISOR"` matches the CHECK constraint in migration T-074.
- `Depends`, `HTTPException`, `status`, `Session` — verify these are already imported before adding; do not duplicate.

## Do not touch

- Any existing line in dependencies.py.
- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.dependencies import get_current_user, require_supervisor, get_auth_service; print('ok')"`
- **Automated**: Verified transitively — TC-208..TC-217 all exercise these deps via router integration tests.
- **DoD**: oauth2_scheme, get_current_user (401 on bad/expired token + inactive user), require_supervisor (403 on non-SUPERVISOR), 5 DI factories. Existing content intact.

## Checkout

> *"dependencies.py modified: oauth2_scheme + get_current_user (401, re-fetches is_active per DS-018) + require_supervisor (403 per DS-019) + 5 V2 DI factories appended. All existing content preserved. Wave 5 router tasks unblocked."*
