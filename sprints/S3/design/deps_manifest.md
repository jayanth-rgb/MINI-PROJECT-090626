# Sprint S3 — Dependency Manifest

**Scope:** backend-only. Frontend deferred to `/ases-ui-scaffold S3`.

## Backend packages

**Zero additions, zero removals, zero bumps.** S3 reuses the existing stack:
- FastAPI 0.115.6
- SQLAlchemy 2.x
- Pydantic v2
- Alembic 1.14.0
- psycopg 3.2.3

The dashboard aggregation and sales report queries use SQLAlchemy's existing expression API (`case()`, `func.sum()`, `select()`, `.in_()`, joined-load relationships).

## Database migrations

**None.** S3 is read-only at the schema layer:
- No new tables
- No new columns
- No new constraints
- No new indexes

Existing indexes (all from S2/T-042) suffice:
- `ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)` — dashboard aggregation date-range scan
- `ix_sales_header_sales_date` — sales report date filter
- `ix_sales_header_dealer` — sales report dealer filter
- `ix_sales_line_dgd(design_id, grade_id, header_id)` — sales report design filter via JOIN

## External services

- **PostgreSQL 16** — reused from S1 docker-compose. No new services.

## Environment variables

| Name | Required | Description |
|---|---|---|
| `DATABASE_URL` | true | Reused from S1 |
| `NEXT_PUBLIC_API_URL` | true | Reused from S1 |

## Frontend packages

Deferred to `/ases-ui-design S3`. Likely candidates if the UI design adds a chart panel:
- `recharts` (small, React-native, MIT)
- `visx` (Airbnb, modular)

Charts are NOT mandated by PRD AC-041..AC-045 — a table layout for the dashboard satisfies the ACs.

## Decisions referenced

DS-002 (now amended by DS-015), DS-003, DS-004, DS-007, DS-010, DS-013, DS-015 (new), DS-016 (new), DS-017 (new)

## Modules touched

| Module | Touch |
|---|---|
| **M-004 Stock Dashboard** | new — 4 files |
| **M-005 Sales Reporting** | new — 3 files |
| **M-001 Master Data** | modify — 1 new method on DesignGradeMapRepository |
| **M-002 Transaction Forms** | modify — 2 new DI factories + main.py mounts (presentation glue only; no business logic change) |

## No breaking changes to

- S1 master CRUD (additive only)
- S2 transaction forms (untouched)
- S2 stock ledger writes (advisory-lock-first + FOR UPDATE pattern intact via DS-015 now spec-text)

## Next

→ `/ases-schema S3`
