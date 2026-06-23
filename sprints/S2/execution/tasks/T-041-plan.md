# T-041 — TimestampMixin upgrade to TIMESTAMPTZ

**Module:** M-007 · **Depends on:** — · **DS:** DS-014 (closes TD-007)

## Why
Closes the TIMESTAMPTZ drift flagged in S1 final-audit (TD-007). Adds explicit `DateTime(timezone=True)` to the mixin so every header that inherits it (S1's 4 master tables + S2's 5 new header/aux tables) carries timezone semantics.

## Implementation logic

```python
# backend/src/infrastructure/db/base.py
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

## Constraints
- DS-014: ORM-level change here; DB-level ALTERs of the 4 S1 columns ship in T-044's migration 0003.
- Do NOT change `server_default` (must remain `func.now()`).
- Do NOT change `nullable` (must remain `False`).
- Do NOT touch `Base` class.

## Do not touch
Any other file.

## Success criteria
- **Manual:** `from src.infrastructure.db.base import TimestampMixin; TimestampMixin.__annotations__['created_at']` resolves; the column type on `Mapped[datetime]` is `DateTime(timezone=True)`.
- **Automated:** Downstream T-042 ORM tests + T-044 migration round-trip created_at with `tzinfo` populated.
- **DoD:** Column type changed; server_default + nullable preserved; Base class untouched.

## Checkout prompt
*"TimestampMixin upgraded to TIMESTAMPTZ. TD-007 closed at the ORM level — DB ALTERs follow in T-044."*
