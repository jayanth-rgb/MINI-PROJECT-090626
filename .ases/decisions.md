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
| DS-013 | Denormalize `place` onto tbl_inward_header + tbl_sales_header (snapshot at save) | architect | M-002, M-007 |
| DS-014 | TimestampMixin emits TIMESTAMPTZ; S2 migration ALTERs S1 4 columns (closes TD-007) | architect | M-007 |
| DS-015 | Stock-ledger writes MUST acquire pg_advisory_xact_lock BEFORE SELECT FOR UPDATE (amends DS-002) | architect | M-002, M-003 |
| DS-016 | Stock Dashboard uses single CASE-aggregated GROUP BY query | architect | M-004 |
| DS-017 | Sales Report shares a single filter-predicate builder across consolidation + transactions queries | architect | M-005 |
| DS-018 | Auth uses JWT (HS256, 8h TTL) via python-jose + passlib bcrypt; no refresh tokens | architect | M-008 |
| DS-019 | Three-role RBAC via enum on tbl_user_master (STAFF / VERIFIER / SUPERVISOR) — no permissions table | architect | M-008 |
| DS-020 | TD-008 (first-row insert race) closed by DS-015 advisory lock; V2 adds TC-207 regression | architect | M-003 |
| DS-021 | Report export uses reportlab (PDF) + openpyxl (Excel) via StreamingResponse | architect | M-010 |
| DS-022 | Invoice unit_price snapshot from tbl_price_master effective_from lookup; zero-price fallback with warning | architect | M-011 |
| DS-023 | Invoices created on-demand by SUPERVISOR (POST /invoices); UNIQUE(sales_header_id); deterministic invoice_number | architect | M-011 |
| DS-024 | V2 auth login wire format is OAuth2 form-encoded per RFC 6749 §4.3.2 (TC bodies are semantic, not JSON) | PO | M-008 |
| DS-025 | V2 non-auth routers use route-level `Depends(get_current_user)` — V1 uses mount-level | PO | M-008 |

See `.ases/decisions.json` for full rationale, tradeoffs, and alternatives considered per decision.
