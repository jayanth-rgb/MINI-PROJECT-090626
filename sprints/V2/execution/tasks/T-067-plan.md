# T-067 — `infrastructure/db/models/auth.py` — UserModel

**Module:** M-008 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

First V2 file. No prior in-sprint tasks. Mirrors the ORM model pattern established in S1 (`models/master.py`) and S2 (`models/transactions.py`). Reads Base + TimestampMixin from `backend/src/infrastructure/db/base.py` (S1). DS-005 (V1 no-auth) is superseded in V2 — this model is the foundation for all V2 auth.

## Implementation logic

```python
# backend/src/infrastructure/db/models/auth.py
from sqlalchemy import Boolean, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TimestampMixin


class UserModel(Base, TimestampMixin):
    __tablename__ = "tbl_user_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("STAFF", "VERIFIER", "SUPERVISOR", name="user_role_enum"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_user_master_username", "username"),
    )
```

## Constraints

- Inherits `TimestampMixin` (DS-014) which provides `created_at` as `DateTime(timezone=True)`.
- `role` must be SQLAlchemy `Enum` type so the migration generates the CHECK constraint correctly (DS-009 ORM-first migration).
- No relationships declared here — auth operations are all by-username lookups, not joined loads.
- No `__repr__` or custom methods — plain data model.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `python -c "from src.infrastructure.db.models.auth import UserModel; print(UserModel.__tablename__, list(UserModel.__table__.c.keys()))"` → `tbl_user_master ['id', 'username', 'password_hash', 'role', 'is_active', 'created_at']`
- **Automated**: T-070 (UserRepository) integration tests (TC-185, TC-186) insert UserModel rows and read them back.
- **DoD**: File exports `UserModel`, inherits Base+TimestampMixin, 5 declared columns + 1 from mixin, UNIQUE on username, Index on username.

## Checkout

> *"UserModel created. tbl_user_master, 5+1 columns, UNIQUE username, TimestampMixin. Ready for T-070 (UserRepository)."*
