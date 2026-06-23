# Sprint S2 — Dependencies Manifest

## Headline
**No new dependencies.** The S1 backend stack (FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, psycopg, pytest, testcontainers[postgres], httpx, ruff) covers everything S2 needs.

## Packages
None added.

## Services
| Service | Role |
|---------|------|
| PostgreSQL 16 | Receives migration 0003 adding 7 tables. Same instance as S1. |
| Docker daemon (testcontainers) | Test-time only — ephemeral PG containers for backend tests. Same as S1. |

## Env vars
All inherited from S1, no changes:
- `DATABASE_URL` — backend connection
- `API_CORS_ORIGINS` — CORS whitelist
- `API_ENV` — environment label

## Frontend
Per LLD's `frontend_ui_track_note`, frontend dependencies will be assessed by `/ases-ui-scaffold S2`. No anticipated new npm packages; S1's set (react-hook-form, zod, axios, tanstack-query, shadcn/radix, sonner, react-day-picker) likely covers the 3 transaction forms.

## Carry-forward acknowledgments

| Item | Status in S2 |
|------|--------------|
| TD-007 (TIMESTAMPTZ) | **Closing in S2 via DS-014** — TimestampMixin upgraded; migration 0003 alters S1 columns + lands new tables as TIMESTAMPTZ from the start. |
| TD-005 / TD-006 (closes on W5) | Unrelated to design; PO action. |
| CF-001 (W5 — long-lived PG bring-up) | Required before `/ases-test-run S2` for live integration. IS-002-style ephemeral PG sufficient for unit + integration tests as in S1. |

## Next step
→ `/ases-schema S2` — formal data schema spec for the 7 new tables, with column types, constraints, indexes, and ER context.
