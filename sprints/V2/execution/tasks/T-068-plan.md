# T-068 — `domain/auth.py` — JWT + bcrypt pure domain functions

**Module:** M-008 · **Wave:** 1 (parallel, no V2 deps) · **Depends on:** —

## Context anchor

Pure domain layer — no SQLAlchemy, no FastAPI, no I/O. Mirrors the isolation principle of `domain/stock.py` (S2). Reads `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_HOURS` from `config.py` (added by sprint-scaffold at CFG-V2-001 resolution). DS-018: HS256 + python-jose + passlib bcrypt.

## Implementation logic

```python
# backend/src/domain/auth.py
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    if not settings.secret_key:
        raise ValueError("SECRET_KEY not configured")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.access_token_expire_hours)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None
```

## Constraints

- `decode_access_token` MUST return `None` on any `JWTError` (expired, malformed, wrong key) — never raise. Callers check for `None` and raise `HTTPException 401`.
- `create_access_token` raises `ValueError` if `SECRET_KEY` is falsy — surfaces misconfiguration at startup rather than at JWT decode time.
- `verify_password` uses `CryptContext.verify()` which is constant-time (bcrypt timing-safe comparison by design).
- Module-level `_pwd_context` created once — avoids repeated CryptContext construction on each call.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `python -c "from src.domain.auth import get_password_hash, verify_password; h=get_password_hash('test'); print(verify_password('test',h), verify_password('wrong',h))"` → `True False`
- **Automated**: TC-171 (verify True), TC-172 (verify False), TC-173 (create_access_token payload), TC-174 (decode expired → None), TC-175 (decode malformed → None).
- **DoD**: 4 functions exported. No class definitions. No SQLAlchemy/FastAPI imports. decode_access_token never raises. bcrypt scheme via passlib.

## Checkout

> *"domain/auth.py created. 4 pure functions: get_password_hash, verify_password, create_access_token, decode_access_token. No I/O. TC-171..175 covered. Ready for T-071 (AuthService)."*
