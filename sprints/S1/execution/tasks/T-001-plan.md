# T-001 — Pydantic Settings (`backend/src/config.py`)

**Module:** M-007 · **Depends on:** none · **TC refs:** none

## Context anchor
- Last completed task: `/ases-sprint-scaffold S1` (skeleton + env-var renames)
- Impacted files: only `backend/src/config.py` (create)
- This is the bedrock — every other backend task imports `get_settings` directly or transitively.

## Implementation logic

```python
# backend/src/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    api_cors_origins: list[str] = []
    api_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Pydantic-settings reads env vars **case-insensitively** matching the field name. So `database_url` reads `DATABASE_URL`, `api_cors_origins` reads `API_CORS_ORIGINS`, `api_env` reads `API_ENV`. `extra='ignore'` lets `.env` contain other lines (DB_HOST, APP_*, LOG_LEVEL) without raising. The `@lru_cache` makes `get_settings()` a singleton — `Depends(get_settings)` in FastAPI returns the same instance for every request, and alembic env.py can import it once.

## Constraints
- DS-001 (stack): pydantic-settings 2.7.0 + python-dotenv 1.0.1 (already installed)
- DS-010 (API versioning): not applicable to this file
- env-var names per analysis ENV-001 fix: `API_CORS_ORIGINS`, `API_ENV` (not `APP_*`)
- Pydantic v2 idioms only — no `class Config: env_file=...` (v1 style)

## Do not touch
- `backend/.env` (PO-owned)
- `backend/.env.example` (already aligned)
- Any other file

## Success criteria
- **Manual:** `backend/.venv/Scripts/python.exe -c "from src.config import get_settings; s = get_settings(); print(type(s).__name__, s.api_env)"` → `Settings development`
- **Automated:** No direct unit test; T-009 conftest verifies indirectly
- **Definition of done:** Imports cleanly; SettingsConfigDict uses `extra='ignore'`; @lru_cache present.

## Checkout prompt
After completion, output exactly: *"Settings + get_settings created in src/config.py. Reads DATABASE_URL, API_CORS_ORIGINS, API_ENV from .env."*
