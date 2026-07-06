# T-073 — `routers/users.py` — SUPERVISOR-only user CRUD

**Module:** M-008 · **Wave:** 5 (after T-089) · **Depends on:** T-071, T-089

## Context anchor

User management is SUPERVISOR-only (DS-019). STAFF and VERIFIER roles receive 403 on all endpoints. DELETE is soft-delete only (DS-008): calls `svc.deactivate_user(user_id)` which sets `is_active=False`, returns 204. `UserUpdate` has all Optional fields so PATCH is safe for partial updates.

## Implementation logic

```python
# backend/src/presentation/api/routers/users.py
from fastapi import APIRouter, Depends, status

from presentation.api.dependencies import get_auth_service, require_supervisor
from application.services.auth_service import AuthService
from presentation.schemas.auth import UserCreate, UserRead, UserUpdate
from infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.create_user(payload)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    svc.deactivate_user(user_id)
```

## Constraints

- All 5 routes use `require_supervisor` — no STAFF/VERIFIER access.
- DELETE is soft-delete only (DS-008): returns 204 with no response body.
- `require_supervisor` chains `get_current_user` — do NOT also add a separate `get_current_user` dep.
- `svc.list_users()` wraps `UserRepository.list_active()` — returns only `is_active=True` users.
- `UserUpdate` all-Optional fields — PATCH is partial-update safe.
- `AuthService.get_user(user_id)` should raise 404 if not found (implement in T-071 scope).

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.users import router; print(len(router.routes))"` → `5`
- **Automated**: TC-211, TC-212
- **DoD**: 5 routes, all SUPERVISOR-gated. Soft-delete (204). AuthService wired.

## Checkout

> *"routers/users.py created. 5 SUPERVISOR-only endpoints (list, create, get, patch, soft-delete). DS-008 soft-delete + DS-019 RBAC enforced. TC-211/212 covered."*
