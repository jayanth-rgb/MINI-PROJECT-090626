# T-069 — `presentation/schemas/auth.py` — Pydantic v2 auth schemas

**Module:** M-008 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Pure Pydantic file. No project imports. Mirrors `schemas/master.py` (S1) and `schemas/transactions.py` (S2) pattern. All schemas consumed by T-071 (AuthService), T-072 (auth router), T-073 (users router).

## Implementation logic

```python
# backend/src/presentation/schemas/auth.py
from typing import Literal
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    role: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    role: Literal["STAFF", "VERIFIER", "SUPERVISOR"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool


class UserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None
    new_password: str | None = None
```

## Constraints

- `UserRead` must have `ConfigDict(from_attributes=True)` — T-071 projects `UserModel` instances through it.
- `UserUpdate` all fields are `None`-default (partial PATCH semantics). AuthService applies only non-None fields.
- `LoginRequest.password` min_length=1 prevents empty-string login attempt reaching bcrypt.
- `UserCreate.password` min_length=8 enforces basic password policy at schema validation time.
- No `password_hash` exposed in `UserRead` — never serialize hashed password to clients.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.presentation.schemas.auth import UserRead; UserRead.model_config['from_attributes']` → `True`
- **Automated**: TC-190 (AuthService.authenticate) returns `TokenResponse`; TC-210 (GET /auth/me) body matches `UserRead` shape.
- **DoD**: 5 schemas exported. No project module imports. UserRead `from_attributes=True`. UserUpdate all optional. No password_hash in any read schema.

## Checkout

> *"schemas/auth.py created. 5 Pydantic v2 schemas: LoginRequest, TokenResponse, UserCreate, UserRead, UserUpdate. Ready for T-071 (AuthService)."*
