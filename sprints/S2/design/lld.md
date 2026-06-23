# Sprint S2 — Low-Level Design

**Sprint:** S2 — Transaction Forms + Stock Ledger
**Features:** F-007 (Inward), F-008 (Sales), F-009 (Adjustment) — 21 ACs (AC-020..AC-040)
**Modules in scope:** M-002 (Transaction Forms), M-003 (Stock Ledger), M-007 (Persistence — schema additions)
**Builds on:** S1 (M-001 master CRUD, DF-006 contract); honors DS-002 (SELECT FOR UPDATE), DS-003 (materialized ledger), DS-004 (on-read carry-forward), DS-007..DS-012

## Architecture at a glance

```
┌────────────────────────────────────────────────────────────────────┐
│ Presentation                                                       │
│   routers: inward.py · sales.py · adjustments.py                   │
│   designs.py (modify: + /grades-with-cb)                           │
│   schemas/transactions.py · dependencies.py (modify) · main.py     │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│ Application                                                        │
│   InwardService · SalesService · AdjustmentService                 │
│   DesignGradeCbService                                             │
│   ⤿ writes header + lines + ledger in ONE SQLAlchemy txn          │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│ Domain (M-003 Stock Ledger)                                        │
│   stock.apply_inward / apply_sale / apply_adjustment               │
│   stock.closing_balance / opening_balance                          │
│   ⤿ SELECT FOR UPDATE on (design_id, grade_id) per DS-002          │
│   ⤿ Forward-recompute for back-dated tx per DS-003                 │
│   ⤿ Carry-forward = prior-month-last-row lookup per DS-004         │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│ Infrastructure                                                     │
│   models/transactions.py — 7 ORM models                            │
│   repositories/transactions.py — incl. StockLedgerRepository       │
│   base.py (modify — TIMESTAMPTZ upgrade, closes TD-007)            │
│   migrations/0003 — alters S1 created_at to TIMESTAMPTZ + creates  │
│                     6 transaction tables + 1 stock_ledger          │
└────────────────────────────────────────────────────────────────────┘
```

## File inventory (16 files: 12 new, 4 modify)

### M-007 — Persistence
1. `backend/src/infrastructure/db/base.py` **(modify)** — TimestampMixin → DateTime(timezone=True). DS-014.
2. `backend/src/infrastructure/db/models/transactions.py` **(new)** — 7 ORM models: InwardHeader/Line, SalesHeader/Line, AdjustmentHeader/Line, StockLedger. Place denormalized on Inward/Sales headers per DS-013.
3. `backend/src/infrastructure/db/repositories/transactions.py` **(new)** — 4 repositories (3 header + StockLedgerRepository with `for_update` SELECT for DS-002).
4. `backend/db/migrations/versions/0003_transaction_and_ledger_tables.py` **(new)** — Alters 4 S1 `created_at` cols to TIMESTAMPTZ; creates 7 new tables + `ix_stock_ledger_dgt` composite index.

### M-003 — Stock Ledger (domain)
5. `backend/src/domain/stock.py` **(new)** — Pure functions: apply_inward, apply_sale, apply_adjustment, closing_balance, opening_balance + private _recompute_forward.

### M-002 — Transaction Forms (application + presentation)
6. `backend/src/application/services/inward_service.py` **(new)** — F-007.
7. `backend/src/application/services/sales_service.py` **(new)** — F-008.
8. `backend/src/application/services/adjustment_service.py` **(new)** — F-009.
9. `backend/src/application/services/design_grade_cb_service.py` **(new)** — DF-003 / AC-036.
10. `backend/src/presentation/schemas/transactions.py` **(new)** — Pydantic Create/Read schemas + DesignGradeReadWithCb.
11. `backend/src/presentation/api/routers/inward.py` **(new)** — POST + GET.
12. `backend/src/presentation/api/routers/sales.py` **(new)** — POST + GET (filters).
13. `backend/src/presentation/api/routers/adjustments.py` **(new)** — POST.
14. `backend/src/presentation/api/routers/designs.py` **(modify)** — add GET `/designs/{id}/grades-with-cb`.
15. `backend/src/presentation/api/dependencies.py` **(modify)** — +4 service factories.
16. `backend/src/main.py` **(modify)** — +3 router mounts.

## New ADRs

### DS-013 — Denormalize `place` on transaction headers
**Why:** PRD AC-022/AC-029 require place to auto-populate from supplier/dealer master and render read-only. Snapshotting the value at save time on tbl_inward_header.place / tbl_sales_header.place gives us:
- Stable historical reads (master place edits don't retroactively change historical transactions)
- One-fewer JOIN at S3 report time
**Tradeoff:** Master-place updates aren't reflected in historical transactions. PO confirms this is the desired semantic — transactions are an immutable historical record.
**Alternatives rejected:** JOIN at read time (forfeits historical immutability).

### DS-014 — Close TD-007 by upgrading TimestampMixin to TIMESTAMPTZ
**Why:** TD-007 flagged the ORM/LLD drift (TIMESTAMP vs TIMESTAMPTZ). S2 introduces 7 new tables — landing them with TIMESTAMPTZ from the start avoids re-introducing the same drift. The 4 S1 `created_at` columns are also altered in the same migration (PG handles this in-place; preserves data).
**Tradeoff:** One-time migration touches S1 tables. Acceptable because (a) the column is server-default-only, no application code writes it, (b) PostgreSQL ALTER COLUMN TYPE TIMESTAMPTZ from TIMESTAMP is non-blocking for our row counts, (c) the alternative (split-policy ORM) creates maintenance burden every time someone adds a new table.
**Alternatives rejected:** Split policy (new TimestampMixinTZ for new tables only) — adds confusion; per-table opt-in — too easy to forget.

## Critical decisions referenced (S1 / pre-S1)

| ID | Relevance to S2 |
|----|------------------|
| DS-002 | SELECT FOR UPDATE on `(design_id, grade_id)` ledger row before each write |
| DS-003 | Materialized `running_balance` column; back-date forward-recompute scoped to (design, grade) and bounded by AC-021 7-day window |
| DS-004 | `opening_balance(m_first)` = `closing_balance(m_first - 1 day)`; no scheduler |
| DS-007 | Strict 4-layer architecture (presentation/application/domain/infrastructure) |
| DS-008 | Soft-delete on masters carries through — transaction tables don't need soft-delete in V1 (immutable historical record per DS-013) |
| DS-009 | ORM is source-of-truth; alembic migrations mirror ORM |
| DS-010 | All routers under `/api/v1` |
| DS-012 | Generic `BaseRepository[TModel]` extends to new entities |

## Atomicity & concurrency

**Atomic write contract:** Each `save_*` service method opens (or joins) the request session and performs `header insert → lines insert → N × stock_ledger inserts` then commits — all-or-nothing. Failure rolls back via FastAPI's `get_db` exception handler.

**Concurrency:** Per DS-002, every ledger insert acquires `SELECT … FOR UPDATE` on the latest row for `(design_id, grade_id)`. Two concurrent saves on the same (design, grade) serialize on this row; PostgreSQL releases the lock at txn commit. Effectively single-writer per (design, grade) — invisible at the project's expected scale per HLD's "single-digit concurrent users".

**Back-dated transactions:** AC-021 limits backdating to 7 days. When `txn_date < latest_row.txn_date`, `_recompute_forward` replays deltas on every later row of the same (design, grade), updating their `running_balance`. Bounded list (≤ ~30 rows at realistic throughput per DS-003).

## Error-mapping summary

| AC / ERR | Where surfaced | Mapped to HTTP |
|----------|----------------|----------------|
| AC-020 / ERR-001 (future date) | service validation | 422 ValidationError |
| AC-021 / ERR-002 (> 7 days prior) | service validation | 422 |
| AC-024 / ERR-007 (nos ≤ 0) | Pydantic + service strip | 422 |
| AC-026 / ERR-006/008 (no valid lines) | service post-strip check | 422 |
| AC-035 / ERR-010 (stock_date > entry_date) | Pydantic model_validator + service | 422 |
| AC-040 / ERR-012 (no active grades for design) | service guard in Adjustment | 422 (router-level translation) |
| Missing master FK | service guard | 404 NotFoundError |

## Frontend UI track (separate)

The 3 form UIs ship via `/ases-ui-design S2` → `/ases-ui-review S2` → `/ases-ui-scaffold S2`. The integration_points the UI track will consume:
- `POST /api/v1/inward`, `POST /api/v1/sales`, `POST /api/v1/adjustments` — save endpoints
- `GET /api/v1/designs/{id}/grades` (S1) — for grade-row auto-population in Inward + Sales (AC-023, AC-031)
- `GET /api/v1/designs/{id}/grades-with-cb?stock_date=…` (new in S2) — for grade-row pre-population in Adjustment (AC-036)

## Next step
→ `/ases-schema S2`
