"""Sprint S1 — shared test infrastructure (resolves INFRA-001).

Three fixtures:

- ``pg_container`` (session-scoped) — brings up a PostgreSQL 16 container via
  testcontainers, runs ``Base.metadata.create_all`` against it, then yields the
  container with engine + URL attached.
- ``db_session`` (function-scoped) — opens a connection inside a top-level
  transaction and yields an SQLAlchemy ``Session``; the transaction is rolled
  back at teardown so every test sees a clean slate without DROP/CREATE.
- ``client`` (function-scoped) — FastAPI ``TestClient`` with ``get_db``
  dependency overridden to yield the per-test ``db_session``.

Runtime requirement: Docker daemon must be running on the host (PO action
DB-001). ``pytest --collect-only`` does not require Docker — only test
execution does.
"""

from __future__ import annotations

import os

# Seed a placeholder DATABASE_URL BEFORE any src.* import so that
# src.config.get_settings() (called at src.infrastructure.db.session import
# time) doesn't fail under tests where no .env file is present. The real per-
# test DB URL comes from the testcontainers postgres in ``pg_container``; this
# placeholder is only used to satisfy Settings validation at import time.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test_placeholder",
)

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from src.infrastructure.db.base import Base

# Importing the model modules materialises all S1 (6 master) + S2 (7 transaction
# + ledger) tables on Base.metadata so create_all sees them. The F401 noqa
# keeps linters quiet about the "unused" imports — they are used for their
# side effect (mapper configuration).
import src.infrastructure.db.models.master  # noqa: F401
import src.infrastructure.db.models.transactions  # noqa: F401


@pytest.fixture(scope="session")
def pg_container() -> Iterator[PostgresContainer]:
    """Spin up PostgreSQL 16 once per test run and apply the schema."""
    with PostgresContainer("postgres:16") as pg:
        # testcontainers defaults to the psycopg2 driver URL; rewrite to the
        # psycopg v3 driver that the project's requirements.txt installs.
        url = pg.get_connection_url().replace(
            "postgresql+psycopg2://", "postgresql+psycopg://"
        )
        engine = create_engine(url, future=True)
        Base.metadata.create_all(engine)
        # Stash both for downstream fixtures.
        pg._engine = engine
        pg._url = url
        yield pg


@pytest.fixture()
def db_session(pg_container: PostgresContainer) -> Iterator[Session]:
    """Per-test SQLAlchemy session inside a rollback-only transaction."""
    conn = pg_container._engine.connect()
    trans = conn.begin()
    SessionLocal = sessionmaker(
        bind=conn,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    """FastAPI TestClient with ``get_db`` overridden to yield ``db_session``."""
    # Lazy imports: src.main is created by T-023 and may not yet exist when
    # earlier tasks reference the conftest. Keeping the import inside the
    # fixture body lets pytest --collect-only succeed today.
    from src.infrastructure.db.session import get_db
    from src.main import app

    def _override() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
