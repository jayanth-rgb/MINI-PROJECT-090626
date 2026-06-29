# Sprint S3 — Schema (Read-only sprint)

**Produced:** 2026-06-25 · **Modules:** M-001 (master reads), M-004 (Stock Dashboard), M-005 (Sales Reporting)

## TL;DR

S3 is a **read-only sprint at the schema layer**:

| Schema change | Count |
|---|---|
| New tables | **0** |
| New columns | **0** |
| New constraints | **0** |
| New indexes | **0** |
| Alembic migrations | **0** |
| Entities reused from S1 + S2 | **7** |
| Indexes already in place from S2 servicing S3 queries | **5** |

S3's dashboard, sales report, and carry-forward verification all consume entities + indexes already shipped in S1 (master tables) + S2 (transaction tables + `tbl_stock_ledger`). The S2 composite index `ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)` was explicitly designed (in S2's schema.json) to also service the S3 Stock Dashboard aggregation — S3 now exercises that prior intent. Likewise the S2 indexes `ix_sales_header_sales_date`, `ix_sales_header_dealer`, `ix_sales_line_dgd` were forward-declared for the S3 Sales Report.

## Entities consumed by S3

| Entity | Source sprint | Module | S3 use |
|---|---|---|---|
| `tbl_stock_ledger` | S2 | M-003 | Dashboard CASE-aggregated SUM + opening/closing latest-as-of lookups |
| `tbl_sales_header` | S2 | M-002 | Sales Report dual-payload (date / dealer / place filters via DS-017) |
| `tbl_sales_line` | S2 | M-002 | Sales Report consolidation GROUP BY + transactions per-line |
| `tbl_design_grade_map` | S1 | M-001 | Dashboard active-pair enumeration (new method `list_active_all`) |
| `tbl_trading_design_master` | S1 | M-001 | Projected `design_name + size` into both response payloads |
| `tbl_grade_master` | S1 | M-001 | Projected `grade_code` + active-pair join filter |
| `tbl_dealer_master` | S1 | M-001 | Projected `dealer_name` into TransactionRow (place comes from header per DS-013) |

## Decisions referenced

- **DS-002** — original SELECT FOR UPDATE serialization (write-side)
- **DS-003** — materialized `running_balance` (closing_balance is O(1) latest-as-of)
- **DS-004** — on-read carry-forward (opening_balance from last-before-month-start row)
- **DS-007** — strict 4-layer architecture (S3 services live in `application/`, no business logic in routers)
- **DS-013** — denormalized `place` snapshot on transaction headers (TransactionRow projects header.place not dealer.place)
- **DS-015** *(new in S3 LLD)* — amend DS-002: advisory-lock-first MUST precede FOR UPDATE on writes (S3 is read-only so DS-015 has no direct effect on S3 code; documented here for reviewer context)
- **DS-016** *(new in S3 LLD)* — single CASE-aggregated GROUP BY for dashboard performance
- **DS-017** *(new in S3 LLD)* — shared filter predicate for sales report guarantees AC-050

## Indexes in play

| Index | Added | S3 uses |
|---|---|---|
| `ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)` | S2 T-042 | Dashboard date-range scan (DS-016); opening_balance + closing_balance latest-as-of |
| `ix_sales_header_sales_date(sales_date)` | S2 T-042 | AC-046 date-range filter (both queries) |
| `ix_sales_header_dealer(dealer_id)` | S2 T-042 | AC-046 dealer multi-select filter |
| `ix_sales_line_dgd(design_id, grade_id, header_id)` | S2 T-042 | AC-047 consolidation GROUP BY + AC-046 design filter |
| `ix_sales_line_header(header_id)` | S2 T-042 | Sales line ↔ header JOIN |
| **(no index on `tbl_sales_header.place`)** | n/a | Place-only filter falls back to seq scan — **acceptable at V1 scale** (single-digit concurrent users per PRD `non_functional.scalability`). V2 candidate if profiling shows place-only filters dominating. |

## Migration plan

```
revision_id: null    (no alembic revision created)
down_revision: 0003_tx_ledger
operations_in_order: []
```

## Completeness check

- ✅ Every persistence-layer LLD file maps to ≥1 schema entity
- ✅ Every schema entity is touched by ≥1 S3 LLD file
- ✅ Non-persistence LLD files (Pydantic schemas, routers, DI, main) correctly excluded from entities
- ✅ Zero entity drift between LLD and schema

## What this means for downstream skills

| Skill | Implication |
|---|---|
| `/ases-test-spec S3` | No schema-shape tests needed (no new tables/columns/indexes/constraints). Tests focus on dashboard formula correctness (FORMULA-001..003), Sales Report filter parity (AC-050), and carry-forward (AC-053). |
| `/ases-sprint-gate S3` | Check `schema_entities_match_lld_models` will resolve to PASS — all 7 entities present + all LLD persistence files audited. |
| `/ases-analyze S3` | No deps drift expected — S3 reuses the existing SQLAlchemy / Alembic / psycopg stack with no new tables to verify. |
| `/ases-sprint-scaffold S3` | No new migration stubs needed (`dependency_changes` block per DS-014 is empty). |
| `/ases-tasks S3` | No DB tasks; only application + presentation tasks. |

## Next

→ `/ases-test-spec S3`
