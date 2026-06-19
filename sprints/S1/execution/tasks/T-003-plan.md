# T-003 — Domain exceptions

**Module:** M-007 · **Depends on:** none · **TC refs:** none

## Context anchor
Foundation file consumed by every service (T-010..T-015) and by the error handler (T-008).

## Implementation logic

```python
# backend/src/domain/exceptions.py

class DomainError(Exception):
    """Base class for all domain errors. Maps to HTTP 500 if no subclass matches."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Repository lookup miss. Maps to HTTP 404."""
    def __init__(self, entity: str, id_: int):
        super().__init__(f"{entity} with id {id_} not found")
        self.entity = entity
        self.id_ = id_


class ConflictError(DomainError):
    """UNIQUE violation (duplicate grade_code, duplicate design-grade pair). Maps to HTTP 409."""
    pass


class ValidationError(DomainError):
    """Domain rule violation not caught by Pydantic. Maps to HTTP 422."""
    pass
```

## Constraints
- DS-007: file lives in `domain/` layer; cannot import from any other project module
- No external deps beyond stdlib

## Do not touch
Any other file.

## Success criteria
- **Manual:** `python -c "from src.domain.exceptions import NotFoundError; raise NotFoundError('Foo', 1)"` raises with message `Foo with id 1 not found`
- **Automated:** Indirectly via TC-017 (ConflictError), TC-027/028 (NotFoundError)
- **DoD:** 4 classes; NotFoundError ctor `(entity, id_)`; ConflictError + ValidationError ctor `(message)`

## Checkout prompt
*"Domain exceptions created — DomainError, NotFoundError, ConflictError, ValidationError. Mapped to HTTP by T-008."*
