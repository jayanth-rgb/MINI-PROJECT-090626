from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.application.services.auth_service import AuthService
from src.infrastructure.db.models.auth import UserModel
from src.presentation.api.dependencies import get_auth_service, get_current_user
from src.presentation.schemas.auth import TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """POST /auth/login — open endpoint (no Bearer token required).

    Accepts form body (application/x-www-form-urlencoded) with fields
    ``username`` and ``password``.  Delegates to AuthService.authenticate
    which raises HTTP 401 on invalid credentials or inactive user.

    TC-208: valid credentials -> 200 TokenResponse with access_token + role.
    TC-209: wrong password -> 401 Unauthorized.
    """
    return svc.authenticate(form.username, form.password)


@router.get("/me", response_model=UserRead)
def me(current_user: UserModel = Depends(get_current_user)) -> UserRead:
    """GET /auth/me — requires a valid Bearer token.

    get_current_user validates the JWT, re-fetches is_active from DB (DS-018),
    and raises HTTP 401 if the token is invalid, expired, or the user is
    deactivated.  Returns UserRead of the authenticated user.

    TC-210: valid token -> 200 UserRead.
    """
    return current_user  # type: ignore[return-value]
