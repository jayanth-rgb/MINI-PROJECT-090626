# T-005 — BaseRepository

**Module:** M-007 · **Depends on:** T-002, T-003 · **TC refs:** indirect

## Context anchor
Generic base for all 6 master repos (T-006). Enforces DS-008 (no delete method) and DS-012 (no raw SQLAlchemy in services).

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/base.py
from typing import Any, Generic, TypeVar, Type
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.base import Base
from src.domain.exceptions import NotFoundError

TModel = TypeVar("TModel", bound=Base)


class BaseRepository(Generic[TModel]):
    model: Type[TModel]

    def __class_getitem__(cls, model: Type[TModel]):
        # When subclassing: class FooRepository(BaseRepository[FooModel]) — bind self.model
        new_cls = type(f"BaseRepository[{model.__name__}]", (cls,), {"model": model})
        return new_cls

    def __init__(self, session: Session):
        self.session = session

    def list(self, include_inactive: bool = False) -> list[TModel]:
        stmt = select(self.model)
        if not include_inactive:
            stmt = stmt.where(self.model.is_active.is_(True))
        return list(self.session.execute(stmt).scalars())

    def get(self, id_: int) -> TModel:
        obj = self.session.get(self.model, id_)
        if obj is None:
            raise NotFoundError(self.model.__name__.removesuffix("Model"), id_)
        return obj

    def create(self, data: dict[str, Any]) -> TModel:
        obj = self.model(**data)
        self.session.add(obj)
        self.session.flush()
        return obj

    def update(self, id_: int, patch: dict[str, Any]) -> TModel:
        obj = self.get(id_)
        for k, v in patch.items():
            if v is not None:  # skip None — partial update
                setattr(obj, k, v)
        self.session.flush()
        return obj

    def soft_delete(self, id_: int) -> TModel:
        obj = self.get(id_)
        obj.is_active = False
        self.session.flush()
        return obj
```

## Constraints
- DS-008: NO `delete()` method anywhere on this class
- DS-012: this is the only persistence-access pattern services may use
- `list()` filters `is_active=True` by default; admin caller passes `include_inactive=True`
- `update()` ignores None values — partial update semantics
- Caller (service) owns commit; repository only `flush()`es

## Do not touch
Any other file.

## Success criteria
- **Manual:** `python -c "from src.infrastructure.db.repositories.base import BaseRepository; print(hasattr(BaseRepository, 'soft_delete'), hasattr(BaseRepository, 'delete'))"` → `True False`
- **Automated:** Covered transitively by all 6 service test files
- **DoD:** soft_delete exists; delete does NOT; NotFoundError raised on miss; partial update skips None

## Checkout prompt
*"BaseRepository[TModel] created — list, get, create, update, soft_delete only. No hard delete (DS-008)."*
