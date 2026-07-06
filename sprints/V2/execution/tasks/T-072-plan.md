# T-072 — `routers/auth.py` — POST /auth/login · GET /auth/me

**Module:** M-008 · **Wave:** 5 (after T-089) · **Depends on:** T-071, T-089

## Context anchor

Auth router is the ONLY router mounted in main.py WITHOUT a global `Depends(get_current_user)` — because `/auth/login` must be publicly accessible. `/auth/me` handles its own auth at route level. AuthService.authenticate handles the 401 on bad credentials (T-071).

## Implementation logic

```python
# backend/src/presentation/api/routers/auth.py
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from presentation.api.dependencies import get_auth_service, get_current_user
from application.services.auth_service import AuthService
from presentation.schemas.auth import TokenResponse, UserRead
from infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: AuthService = Depends(get_auth_service),
):
    return svc.authenticate(form.username, form.password)


@router.get("/me", response_model=UserRead)
def me(current_user: UserModel = Depends(get_current_user)):
    return current_user
```

## Constraints

- `POST /login` uses `OAuth2PasswordRequestForm` — form body (`Content-Type: application/x-www-form-urlencoded`), fields are `username` and `password`. FastAPI handles parsing.
- `POST /login` has NO `get_current_user` dependency — must remain publicly accessible.
- `GET /me` uses `get_current_user` at route level (not injected from router mount in main.py).
- `response_model=TokenResponse` on login — do not return a raw dict.
- `TokenResponse` contains `access_token`, `token_type='bearer'`, `role` — all populated by `AuthService.authenticate`.

## Do not touch

- Any other file.

## Success criteria

- **Manual**: `python -c "from src.presentation.api.routers.auth import router; print([r.path for r in router.routes])"` → `['/login', '/me']`
- **Automated**: TC-208, TC-209, TC-210
- **DoD**: 2 routes. /login open. /me auth-protected at route level. AuthService.authenticate called on /login.

## Checkout

> *"routers/auth.py created. POST /auth/login (open, OAuth2PasswordRequestForm) + GET /auth/me (get_current_user dep). TC-208/209/210 covered. Router ready for include_router in T-092."*
