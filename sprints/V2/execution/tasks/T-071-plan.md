# T-071 — `services/auth_service.py` — AuthService

**Module:** M-008 · **Wave:** 3 (after T-067, T-068, T-069, T-070) · **Depends on:** T-067, T-068, T-069, T-070

## Context anchor

Application layer auth business logic. DS-018: JWT 8h TTL, bcrypt; `get_current_user` re-fetches `is_active` from DB on every call (so deactivation takes effect within one request — not at token expiry). All DB access via UserRepository; password ops via domain.auth.

## Implementation logic

```python
# backend/src/application/services/auth_service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domain.auth import verify_password, create_access_token, decode_access_token, get_password_hash
from infrastructure.db.models.auth import UserModel
from infrastructure.db.repositories.auth import UserRepository
from presentation.schemas.auth import TokenResponse, UserCreate, UserUpdate


class AuthService:

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> TokenResponse:
        user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid credentials")
        token = create_access_token(data={"sub": user.username, "role": user.role})
        return TokenResponse(access_token=token, token_type="bearer", role=user.role)

    def get_current_user(self, token: str) -> UserModel:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        return user

    def create_user(self, data: UserCreate) -> UserModel:
        if self._repo.get_by_username(data.username) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Username '{data.username}' already exists")
        user = UserModel(
            username=data.username,
            password_hash=get_password_hash(data.password),
            role=data.role,
            is_active=True,
        )
        return self._repo.create(user)

    def list_users(self) -> list[UserModel]:
        return self._repo.list_active()

    def update_user(self, user_id: int, data: UserUpdate) -> UserModel:
        user = self._repo.get(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User {user_id} not found")
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.role is not None:
            user.role = data.role
        if data.new_password is not None:
            user.password_hash = get_password_hash(data.new_password)
        return self._repo.update(user)
```

## Constraints

- `authenticate` returns the **same** 401 message for "not found", "inactive", and "wrong password" — security through uniformity (prevents username enumeration).
- `get_current_user` re-fetches from DB even if `sub` is in the JWT — this is intentional (DS-018: deactivation takes effect within one request).
- `create_user` performs a pre-insert uniqueness SELECT to return a clean 409 (rather than catching IntegrityError from the UNIQUE constraint).
- `update_user` applies only non-`None` fields — supports partial PATCH semantics.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.application.services.auth_service import AuthService; print(len([m for m in dir(AuthService) if not m.startswith('_')]))` ≥ 5
- **Automated**: TC-190 (valid creds → TokenResponse), TC-191 (wrong pass → 401), TC-192 (inactive → 401), TC-193 (valid JWT → UserModel), TC-194 (dup username → 409).
- **DoD**: 5 methods. authenticate uses same 401 message for all failure modes. get_current_user re-fetches is_active. create_user hashes password. update_user partial-patch safe.

## Checkout

> *"AuthService created. 5 methods covering login, token validation, user CRUD. TC-190..TC-194 covered. Ready for T-072 (auth router) + T-073 (users router)."*
