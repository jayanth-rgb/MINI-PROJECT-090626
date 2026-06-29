# Sprint S3 — Codebase Analysis

**Produced by:** `/ases-analyze S3`
**Date:** 2026-06-26
**Verdict:** **READY**
**Next:** `/ases-sprint-scaffold S3`

---

## Scope under test

| Metric | Value |
|---|---|
| LLD files total | 10 |
| LLD files NEW | 7 |
| LLD files MODIFY | 3 |
| Modules (new) | M-004 Dashboard · M-005 Sales Report |
| Modules (modified) | M-001 Master · M-002 API mounts |
| Features | F-010 Stock Dashboard · F-011 Sales Report · F-012 Carry-Forward (read-only verification) |
| New backend packages | 0 |
| New migrations | 0 |
| New env vars | 0 |

---

## Checks performed

### 1. `deps_manifest_packages_vs_installed` — PASS
`deps_manifest.packages = []`. Spot-checked the backend venv at `backend/.venv`:

```
fastapi=0.115.6  sqlalchemy=2.0.36  pydantic=2.10.4  alembic=1.14.0
psycopg=3.2.3    pytest=8.3.4       uvicorn=0.34.0   httpx=0.28.1
```

All match `scaffold.installed_packages`. Every S3 LLD import (`sqlalchemy.case`, `sqlalchemy.func.sum`, `sqlalchemy.select`, `.in_`, `pydantic.BaseModel`, `pydantic.ConfigDict`, `fastapi.APIRouter`, `fastapi.Query`, `fastapi.Depends`, `datetime`) resolves against the existing stack.

### 2. `deps_manifest_migrations_vs_alembic_versions` — PASS
`deps_manifest.migrations = []`. S3 is read-only at the schema layer — no alembic revision file is expected. Existing migrations (`0001_baseline.sql`, `0002_master_tables.py`, `0003_transaction_and_ledger_tables.py`) intact.

### 3. `lld_files_new_do_not_pre_exist` — PASS
All 7 new LLD files are absent from the working tree — safe to create in `/ases-dev`:

- `backend/src/presentation/schemas/dashboard.py`
- `backend/src/infrastructure/db/repositories/ledger_aggregates.py`
- `backend/src/application/services/dashboard_service.py`
- `backend/src/presentation/api/routers/dashboard.py`
- `backend/src/presentation/schemas/sales_report.py`
- `backend/src/application/services/sales_report_service.py`
- `backend/src/presentation/api/routers/sales_report.py`

### 4. `lld_files_modified_exist_with_expected_surface` — PASS
All 3 modify targets present the surface the LLD expects to extend (purely additive — zero shared-line edits):

| File | Existing surface | Additive change |
|---|---|---|
| `backend/src/infrastructure/db/repositories/master.py` | `DesignGradeMapRepository.list_active_by_design` (S1) at line 46 | Add sibling `list_active_all()` |
| `backend/src/presentation/api/dependencies.py` | 10 DI factories (supplier · staff · dealer · grade · design · design_grade_map · inward · sales · adjustment · design_grade_cb) | Add `get_dashboard_service` + `get_sales_report_service` |
| `backend/src/main.py` | 9 `include_router` calls + CORS + error handlers + `/health` | Add `dashboard` + `sales_report` routers under `/api/v1` |

### 5. `lld_depends_on_resolves_to_existing_code` — PASS
Every `depends_on[]` edge in the LLD resolves:

- `backend/src/infrastructure/db/models/transactions.py` (S2 T-042) ✓
- `backend/src/infrastructure/db/repositories/base.py` (S1) ✓
- `backend/src/domain/stock.py` (S2) — `opening_balance` (line 134), `closing_balance` (line 123), advisory-lock-first `_apply` (line 23) all present
- `backend/src/infrastructure/db/models/master.py` (S1) ✓
- `backend/src/infrastructure/db/session.py` (S1) with `get_db` ✓

### 6. `s2_composite_indexes_present` — PASS
S3 query plans (DS-016 dashboard SUM-over-window, DS-017 sales-report joins) depend on four composite indexes — all confirmed:

| Index | Source |
|---|---|
| `ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)` | `models/transactions.py:255` + migration 0003:287 |
| `ix_sales_header_sales_date(sales_date)` | `models/transactions.py:115` + migration 0003:103 |
| `ix_sales_header_dealer(dealer_id)` | `models/transactions.py:116` + migration 0003:108 |
| `ix_sales_line_dgd(design_id, grade_id, header_id)` | `models/transactions.py:144` + migration 0003:213 |

### 7. `env_vars_present_in_env_example` — PASS
| Var | File | Line | Required by |
|---|---|---|---|
| `DATABASE_URL` | `backend/.env.example` | 4 | Backend startup (inherited S1) |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.example` | 5 | Next.js client (inherited S1) |

No new env vars introduced for S3.

### 8. `no_drift_from_previous_sprints` — PASS
S1 master CRUD surface and S2 transactions surface intact at their respective scaffold-spec / TD-011-fix versions. No file from a closed sprint has unexplained modifications since commit `68a675e` (S2 release).

### 9. `carry_forward_items_acknowledged` — PASS
- **W5 / CF-001** (PO PG bring-up) — does not block S3 dev (testcontainers covers test paths).
- **TD-001 / TD-010** (UI-track items) — belong to `/ases-ui-scaffold S3`, not `/ases-tasks`.

---

## Blocking gaps

**None.**

---

## Non-blocking gaps

### NB-S3-001 · Knowledge graph is stale (impact: low)
`graphify-out/` was built at commit `91d39423` (S1 era); current HEAD is `df03a51` (S2 release). The graph predates S2 transactions/ledger code that S3 reads against. Not required by `/ases-tasks`, but `/ases-critique` benefits from a fresh graph.
**Resolution:** run `/ases-graphify` before `/ases-tasks` (AST-only — no LLM cost).

### NB-S3-002 · PG bring-up still pending (impact: low — carry-forward from S1 W5)
Long-lived PostgreSQL bring-up + `alembic upgrade head` + seed run still pending PO action. Does **not** block `/ases-dev` or `/ases-test-run` (testcontainers handles test PG). Only required for out-of-band manual API smoke tests of the new endpoints.
**Resolution:** PO: `cd backend && docker-compose up -d db && alembic upgrade head && python -m scripts.seed_master`. Independent of S3 execution.

### NB-S3-003 · UI-track tech-debt (impact: negligible)
TD-001 (shadcn calendar patch) and TD-010 (Radix Select/Popover jsdom incompatibility — 7 TCs deferred from S2) list `target_sprint='S3'`. They belong to the UI track and surface at `/ases-ui-scaffold S3`, not at `/ases-tasks`.
**Resolution:** address in the UI track when `/ases-ui-design S3` begins.

---

## Codebase drift
None detected.

---

## Verdict

**READY** — S3 design is internally consistent and aligns with the current codebase: zero new backend packages, zero new migrations, zero new env vars, 7 net-new files do not collide, 3 modify-targets exist with stable surfaces, and every S2 index + domain primitive that S3 reads against is in place.

**Next:** `/ases-sprint-scaffold S3`
**PO approval:** not required (PASS verdict, zero blocking gaps).
