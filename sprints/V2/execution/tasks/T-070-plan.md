# T-070 — `infrastructure/db/repositories/auth.py` — UserRepository

**Module:** M-008 · **Wave:** 2 (after T-067) · **Depends on:** T-067 (UserModel)

## Context anchor

Extends `BaseRepository[UserModel]` (S1) with auth-specific finders. Same pattern as `SupplierRepository`, `GradeRepository` etc from S1. DS-012: services depend on repositories — AuthService never constructs queries directly.

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/auth.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models.auth import UserModel
from infrastructure.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, UserModel)

    def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.username == username).limit(1)
        return self._db.scalar(stmt)

    def list_active(self) -> list[UserModel]:
        stmt = (
            select(UserModel)
            .where(UserModel.is_active == True)
            .order_by(UserModel.username.asc())
        )
        return list(self._db.scalars(stmt).all())
```

## Constraints

- `get_by_username` is case-sensitive (PostgreSQL default varchar equality). No `.lower()` normalization — usernames are stored as entered.
- Returns `None` (not raises) when not found — AuthService converts to `HTTPException 401`.
- `list_active` only returns `is_active=True` rows — soft-deleted users are invisible here. Admin deactivation takes effect on next `list_active` call.
- BaseRepository provides `create()`, `update()`, `get(id)`, `soft_delete(id)` — no need to re-implement them.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.infrastructure.db.repositories.auth import UserRepository; print(hasattr(UserRepository, 'get_by_username'), hasattr(UserRepository, 'list_active'))` → `True True`
- **Automated**: TC-185 (seeded user returned), TC-186 (unknown username → None).
- **DoD**: `UserRepository` exported. Two new methods. Inherits `BaseRepository[UserModel]`. No raw SQL.

## Checkout

> *"UserRepository created. get_by_username (case-sensitive LIMIT 1) + list_active (active only ASC). Ready for T-071 (AuthService)."*
