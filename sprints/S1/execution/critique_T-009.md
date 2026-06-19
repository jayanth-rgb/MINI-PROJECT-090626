# T-009 — Critique

**Produced by:** `/ases-critique T-009 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-009.json](./critique_T-009.json)
**Reviewed files:**
- [backend/tests/conftest.py](../../../backend/tests/conftest.py)
- [backend/requirements-dev.txt](../../../backend/requirements-dev.txt)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 3 fixtures, psycopg v3 URL rewrite, lazy main import |
| Contract | **PASS** — all downstream tests (services + integration) will pick up the fixtures by name |
| Test | **PASS** — `pytest --collect-only` clean; `pytest --fixtures` shows all 3 |
| Security | **PASS** — test-only file; ephemeral container creds |
| Structural | PASS |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

**Gap resolution:** INFRA-001 → ✅ RESOLVED.

---

## Lens-by-lens

### 1 · Spec — PASS

| Fixture | Scope | Behaviour |
|---------|-------|----------|
| `pg_container` | session | spins up `postgres:16`; rewrites URL to psycopg v3; runs `Base.metadata.create_all`; stashes engine + url for downstream fixtures |
| `db_session` | function | opens a connection + outer transaction; yields a Session bound to it; rolls back at teardown |
| `client` | function | overrides `app.dependency_overrides[get_db]` to yield the per-test `db_session`; clears overrides in `finally` |

Models import (`import src.infrastructure.db.models.master  # noqa: F401`) is for `Base.metadata` side effect — registers all 6 tables before `create_all`.

### 2 · Contract — PASS

Downstream consumers:

| Test family | Fixture | OK? |
|------------|---------|-----|
| Service unit tests (TC-001..TC-032) | `db_session` | ✓ |
| DB constraint tests (TC-018, TC-026) | `db_session` | ✓ |
| Integration tests (TC-033..TC-038) | `client` | ✓ |

All imports used: typing, pytest, fastapi.testclient, sqlalchemy, testcontainers, Base + models (T-002 + T-004 deps). `from src.main import app` + `from src.infrastructure.db.session import get_db` are lazy inside the `client` fixture body.

### 3 · Test — PASS

`/ases-dev` smokes:

```
$ pytest tests/ --collect-only
no tests collected in 0.10s        ← clean import, zero tests yet

$ pytest tests/ --fixtures | grep -E '^(pg_container|db_session|client)'
pg_container [session scope] -- tests\conftest.py:38
db_session -- tests\conftest.py:55
client -- tests\conftest.py:75
```

pip install added testcontainers 4.9.0, docker 7.1.0, and supporting deps to `backend/.venv` cleanly.

### 4 · Security — PASS

- Test-only file; not in production code path.
- testcontainers spawns ephemeral container with random credentials → no hardcoded passwords.
- `trans.rollback()` in `finally` guarantees no leakage of test data between tests.
- `app.dependency_overrides.clear()` in `finally` keeps dependency-override state isolated per test.
- No raw SQL; schema managed via SQLAlchemy DDL.

### 5 · Structural — PASS

Single conftest with 3 fixtures + 2 attribute stashes on the container. Inbound deps satisfied (T-002, T-004). Outbound: every future test file in `backend/tests/**` will reference these fixtures by name.

---

## Soft notes (non-blocking)

### N-001 · "SAVEPOINT pattern" label is shorthand

Plan.md calls the isolation strategy "SAVEPOINT-rolled-back" but the code uses `conn.begin()` (a top-level connection transaction), **not** `conn.begin_nested()` (the actual SAVEPOINT API).

Functionally equivalent for test isolation: the outer transaction wraps everything the service does, and `trans.rollback()` reverts the lot — including any `Session.commit()` calls (which only end the session-level subtransaction). This is the canonical pattern from the SQLAlchemy docs (*Joining a Session into an External Transaction*). Logged so a future contributor doesn't "fix" it by adding `begin_nested()`.

### N-002 · `pg._engine` / `pg._url` are protected attribute writes

testcontainers' `PostgresContainer` has no public hook for stashing the engine. The fixture writes `_engine` and `_url` (underscore-prefixed) to pass them to the `db_session` fixture. Risk is low (testcontainers unlikely to evolve those exact names) but flagged for sprint-close revisit if testcontainers ever ships a breaking change.

### N-003 · Docker required at runtime

Manifest writes, `pip install`, and `pytest --collect-only` all work without Docker. Running any test that actually uses `pg_container` requires the Docker daemon (PO action DB-001). Echoed here so `/ases-test-run S1` doesn't surprise the PO.

---

## Disposition

Mark T-009 `status=complete` in [tasks.json](./tasks.json). Flip **INFRA-001** to RESOLVED in [.ases/context.json](../../../.ases/context.json) `open_issues`. Proceed to **`/ases-validate T-010 S1`** — `SupplierService`. All service-layer deps (T-003, T-006, T-007) are complete; the service execution batch begins.
