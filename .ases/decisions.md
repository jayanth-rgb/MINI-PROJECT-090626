# Architectural Decision Records — Jayanth Trading Tiles System

> Auto-generated companion to `.ases/decisions.json` · 2026-06-09

| ID | Decision | Made by | Modules |
|---|---|---|---|
| DS-001 | Stack: FastAPI + Next.js + PostgreSQL + Docker | PO | all |
| DS-002 | SELECT FOR UPDATE on stock_ledger per (design, grade) write | architect | M-003 |
| DS-003 | Materialised running balance in tbl_stock_ledger (not live SUM) | architect | M-003, M-004 |
| DS-004 | Monthly carry-forward as on-read lookup, not scheduled job | architect | M-003, M-004 |
| DS-005 | V1 ships without authentication — trusted internal network only | PO | M-006 |
| DS-006 | Frontend and backend ship as separate Docker images | architect | M-006, M-007 |
| DS-007 | Backend strict four-layer architecture (presentation/application/domain/infrastructure) | architect | M-001..M-007 |
| DS-008 | Soft-delete only in V1 — HTTP DELETE maps to `is_active=false`, no hard delete | architect | M-001, M-007 |
| DS-009 | Alembic autogenerate with ORM as source of truth; no hand-written DDL | architect | M-007 |
| DS-010 | API base path `/api/v1`; breaking changes will introduce `/api/v2` | architect | M-001..M-006 |
| DS-011 | Admin forms via react-hook-form + Zod + shadcn primitives — no `form.tsx` shim (closes TD-002) | architect | M-006 |
| DS-012 | Generic `BaseRepository[TModel]` over per-entity hand-written CRUD | architect | M-001, M-007 |

See `.ases/decisions.json` for full rationale, tradeoffs, and alternatives considered per decision.
