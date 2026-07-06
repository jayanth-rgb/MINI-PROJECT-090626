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
# V2 / DS-025: JWT-signing key required at import time so create_access_token()
# below can build the default supervisor Bearer token used by the ``client``
# fixture. Same placeholder pattern as DATABASE_URL — real deployments override
# via .env.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-v2-tests")

from datetime import timedelta
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
import src.infrastructure.db.models.auth  # noqa: F401  # V2 T-067
import src.infrastructure.db.models.pricing  # noqa: F401  # V2 T-079

from src.domain.auth import create_access_token, get_password_hash
from src.infrastructure.db.models.auth import UserModel

# V2 / DS-025 — precompute the default supervisor password hash once at module
# load. Bcrypt is intentionally slow (~200 ms per hash); reusing this constant
# across every ``client`` fixture instantiation keeps the S1/S2/S3 suite time
# from ballooning.
_DEFAULT_SUPERVISOR_USERNAME = "__test_default_supervisor__"
_DEFAULT_SUPERVISOR_PASSWORD_HASH = get_password_hash("test-default-pw")


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
    """FastAPI TestClient with ``get_db`` overridden and a default SUPERVISOR JWT.

    Per DS-025 the 11 V1 routers now carry a mount-level
    ``Depends(get_current_user)``. To keep pre-V2 tests (S1/S2/S3 API,
    integration scenarios, system tests) driving V1 endpoints, this fixture
    seeds a single SUPERVISOR user into the per-test ``db_session`` and
    attaches a matching Bearer token to the TestClient's default headers.
    Per-request ``headers={"Authorization": ...}`` overrides still work — the
    V2 role-based tests (e.g. TC-211 STAFF, TC-212 admin) supply their own
    tokens and those take precedence over the default.
    """
    from src.infrastructure.db.session import get_db
    from src.main import app

    def _override() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override

    db_session.add(
        UserModel(
            username=_DEFAULT_SUPERVISOR_USERNAME,
            password_hash=_DEFAULT_SUPERVISOR_PASSWORD_HASH,
            role="SUPERVISOR",
            is_active=True,
        )
    )
    db_session.flush()

    token = create_access_token(
        data={"sub": _DEFAULT_SUPERVISOR_USERNAME, "role": "SUPERVISOR"},
        expires_delta=timedelta(hours=8),
    )

    try:
        with TestClient(app) as c:
            c.headers.update({"Authorization": f"Bearer {token}"})
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def unauthenticated_client(db_session: Session) -> Iterator[TestClient]:
    """TestClient with no default Authorization header.

    Use this only for tests that assert the V1 auth guard (DS-025) — every
    other test should use ``client``. ``get_db`` is still overridden so the
    request path can execute far enough for the guard to reject it.
    """
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
