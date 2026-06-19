# T-001 — Tests

**No dedicated unit tests** for this task — the Settings pattern is library-level and indirectly verified by the integration test suite (TC-033..038 all boot the FastAPI app, which imports config).

## Manual verification

```powershell
cd "e:/MY NEW MINI PROJECT/MINI PROJECT 090626"
backend/.venv/Scripts/python.exe -c "from src.config import get_settings; s = get_settings(); print(type(s).__name__, s.api_env)"
```

Expected output: `Settings development`

If it fails with `ValidationError: DATABASE_URL required` → PO must `cp backend/.env.example backend/.env` and set DB_PASSWORD first.

## Coverage chain

- TC-033 / TC-034 / TC-035 / TC-036 / TC-037 / TC-038 — integration tests that boot `app = create_app()` which calls `get_settings()` transitively.
