# T-008 — Critique

**Produced by:** `/ases-critique T-008 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-008.json](./critique_T-008.json)
**Reviewed file:** [backend/src/presentation/api/errors.py](../../../backend/src/presentation/api/errors.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — `register_error_handlers` + 4 handlers match LLD `files[15]` |
| Contract | **PASS** — T-023 `main.py` factory will mount cleanly |
| Test | **PASS** — TC-034/035/038 verified inline via TestClient |
| Security | **PASS** — IntegrityError detail kept generic; no schema leak |
| Structural | PASS |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

---

## Lens-by-lens

### 1 · Spec — PASS

| Exception | Status | Body shape |
|-----------|--------|------------|
| `NotFoundError` (domain) | 404 | `{"detail": exc.message}` |
| `ConflictError` (domain) | 409 | `{"detail": exc.message}` |
| `ValidationError` (domain) | 422 | `{"detail": exc.message}` |
| `IntegrityError` (sqlalchemy.exc) | 409 | `{"detail": "unique constraint violation"}` |

All 4 use `async def` handlers — matches FastAPI modern idiom.

### 2 · Contract — PASS

| Downstream | Usage | OK? |
|-----------|-------|-----|
| T-023 `main.py create_app()` | `register_error_handlers(app)` | ✓ |
| T-009 `tests/conftest.py` (TestClient) | inherits handlers via mounted app | ✓ |

Imports: `fastapi.{FastAPI, Request}`, `fastapi.responses.JSONResponse`, `sqlalchemy.exc.IntegrityError`, `src.domain.exceptions.{NotFoundError, ConflictError, ValidationError}` — all used.

### 3 · Test — PASS

Inline TestClient verification during `/ases-dev`:

| Exception raised | Status | Body |
|------------------|--------|------|
| `NotFoundError('Supplier', 999)` | 404 | `{"detail": "Supplier with id 999 not found"}` |
| `ConflictError("grade_code '1' already exists")` | 409 | `{"detail": "grade_code '1' already exists"}` |
| `ValidationError('bad input')` | 422 | `{"detail": "bad input"}` |
| `IntegrityError(...)` | 409 | `{"detail": "unique constraint violation"}` |

All match TC-034/035/038 expected output. **Note:** TC-035/038 assertions look for substrings (`grade_code`, `design_id, grade_id`) in the 409 detail — these come via the **ConflictError** path (service pre-check), not the IntegrityError safety-net. In tests the pre-check always wins; IntegrityError is the production race fallback.

### 4 · Security — PASS

- **IntegrityError detail is hardcoded** to `"unique constraint violation"` — does not leak SQL statement, constraint name, or table internals.
- `NotFoundError` detail: `"Entity with id N not found"` — `entity` is service-controlled (e.g. `'Supplier'`), `id_` is typed `int`. No injection/XSS surface.
- `ConflictError` / `ValidationError` detail: domain-constructed strings from Pydantic-validated payloads. No raw user input echoed.
- JSON response uses FastAPI's default encoder → safe escaping; frontend toast renders as text not HTML.
- No stack traces or exception classes exposed to clients.

### 5 · Structural — PASS

Single file, one function with 4 nested closures. All imports used. Inbound: `src.domain.exceptions` (T-003 ✓). Outbound to T-023 forming when `main.py` lands.

---

## Soft notes (non-blocking)

### N-001 · Two `ValidationError` classes coexist

`src.domain.exceptions.ValidationError` (T-003) shares the class **name** with `pydantic.ValidationError`. FastAPI dispatches handlers on exact class identity, so both work independently:

- `pydantic.ValidationError` → FastAPI's built-in 422 with list-of-errors body (auto-handled).
- `src.domain.exceptions.ValidationError` → our handler with `{"detail": exc.message}`.

Logged so future contributors don't "fix" the name overlap — both paths are intentional.

### N-002 · IntegrityError generic detail vs test expectations

TC-035 and TC-038 expect the 409 body to contain substrings like `'grade_code'` or `'design_id, grade_id'`. Those substrings come from the **ConflictError** path (service pre-check), not from `IntegrityError`. Tests run serially so the pre-check always fires first.

In production, the `IntegrityError` path is a race-safety net. Sprint-close consideration: if observed in prod, parse `exc.orig.constraint_name` to emit a less leaky but more informative detail (e.g. `"duplicate grade_code"`). Out of scope for S1.

---

## Disposition

Mark T-008 `status=complete` in [tasks.json](./tasks.json). Proceed to **`/ases-validate T-009 S1`** — testcontainers conftest (resolves INFRA-001 analysis gap).
