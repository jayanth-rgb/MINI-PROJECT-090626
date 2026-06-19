# T-009 — Tests

No dedicated test for the fixtures themselves; they are exercised by every downstream test.

## Manual verification

```powershell
backend/.venv/Scripts/pip install -r backend/requirements-dev.txt
# → Successfully installed testcontainers-4.9.0 ...

backend/.venv/Scripts/python.exe -m pytest backend/tests/ --collect-only 2>&1 | head -10
# → no errors
```

## Docker dependency (DB-001)
testcontainers requires a running Docker daemon. If `pytest` reports `cannot connect to Docker` → start Docker Desktop or pass `TESTCONTAINERS_RYUK_DISABLED=true` in CI.

## Coverage
This fixture set underpins TC-005, TC-006, TC-018, TC-019, TC-024..032, TC-033..038 — 24 of 46 test cases.
