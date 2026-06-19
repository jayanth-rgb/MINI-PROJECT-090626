# Backend — Jayanth Trading Tiles System

FastAPI 0.115 + SQLAlchemy 2.0 + PostgreSQL 16.

## Layout
- `src/` — application package (created per task in S1)
- `db/bootstrap.sql` — Postgres init (extensions + grants)
- `db/migrations/` — Alembic migrations (initialized in S1)
- `tests/{unit,integration,system}/` — pytest suites

## Run via Docker (recommended)
From project root:

    cp .env.example .env       # fill DB_PASSWORD
    docker-compose up -d db
    docker-compose up backend

## Run via venv (local IDE workflow)

    python -m venv .venv
    .venv\Scripts\activate     # Windows
    pip install -r requirements-dev.txt
    cp .env.example .env
    uvicorn src.main:app --reload

The actual `src/main.py` is created in S1; until then `import src.main` will fail.
