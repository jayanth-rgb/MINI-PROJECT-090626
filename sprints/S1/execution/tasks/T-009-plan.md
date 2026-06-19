# T-009 — Test Infrastructure

**Module:** M-007 · **Depends on:** T-002 · **TC refs:** none (infra) · **Resolves:** INFRA-001

## Context anchor
This task makes the rest of the sprint testable. After T-009 every service test can spin up a real PostgreSQL via testcontainers and roll back per-test.

## Implementation logic

### Step 1 — append to `backend/requirements-dev.txt`

```
# Append exactly one line (after existing dev deps):
testcontainers[postgres]==4.9.0
```

Then `backend/.venv/Scripts/pip install -r backend/requirements-dev.txt`.

### Step 2 — write `backend/tests/conftest.py`

```python
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from src.infrastructure.db.base import Base
import src.infrastructure.db.models.master  # noqa: F401 — ensure Base.metadata sees models


@pytest.fixture(scope="session")
def pg_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        engine = create_engine(url, future=True)
        Base.metadata.create_all(engine)
        pg._engine = engine  # stash for use in db_session
        pg._url = url
        yield pg


@pytest.fixture()
def db_session(pg_container) -> Iterator[Session]:
    """Per-test session inside a SAVEPOINT — rolls back at teardown."""
    conn = pg_container._engine.connect()
    trans = conn.begin()
    SessionLocal = sessionmaker(bind=conn, autoflush=False, autocommit=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture()
def client(db_session) -> Iterator[TestClient]:
    """FastAPI TestClient with get_db overridden to yield the per-test session."""
    from src.main import app
    from src.infrastructure.db.session import get_db

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## Constraints
- Only `requirements-dev.txt` is touched on the manifest side
- Fixture names are stable contracts — every downstream test imports them
- Session scope on container; function scope on db_session for per-test isolation
- SAVEPOINT pattern keeps tests deterministic without DROP/CREATE between cases

## Do not touch
- `backend/requirements.txt`
- Any source file

## Success criteria
- **Manual:** `backend/.venv/Scripts/pip install -r backend/requirements-dev.txt` succeeds; `backend/.venv/Scripts/python.exe -m pytest backend/tests/ --collect-only 2>&1 | head -5` shows collected tests
- **Automated:** Every subsequent test uses these fixtures
- **DoD:** 3 fixtures (pg_container, db_session, client); manifest updated

## PO ack required
testcontainers requires Docker daemon on the host. PO must have completed DB-001 (Docker installed) before tests run. This task delivers the code; runtime needs Docker up.

## Checkout prompt
*"Test infrastructure ready — testcontainers-postgres + 3 conftest fixtures (pg_container, db_session, client). INFRA-001 resolved."*
