# T-002 — Tests

**No dedicated unit tests.** Trio is infrastructure scaffolding; correctness verified via downstream tasks.

## Manual verification

```powershell
backend/.venv/Scripts/python.exe -c "from src.infrastructure.db.base import Base; from src.infrastructure.db.session import engine, SessionLocal, get_db; print('ok')"
# → ok

cd backend && backend/.venv/Scripts/alembic.exe check
# → exit 0 (no pending changes; Base.metadata is empty until T-004)
```

If alembic check errors with "Can't locate revision identified by ..." → run `alembic stamp head` once against the seed baseline.

## Indirect coverage
- T-005 BaseRepository tests use SessionLocal
- T-009 conftest builds the test DB via Base.metadata.create_all
- T-024 verifies env.py through `alembic upgrade head`
