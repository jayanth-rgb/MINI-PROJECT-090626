# Sprint S2 — Data Schema

**Sprint:** S2 · **Modules:** M-002 (transaction forms), M-003 (stock ledger), M-007 (persistence)
**Entities added:** 7 tables · **S1 columns altered:** 4 `created_at` (TIMESTAMP → TIMESTAMPTZ per DS-014)
**Reference ADRs:** DS-002 SELECT FOR UPDATE · DS-003 materialized ledger · DS-004 carry-forward · DS-009 ORM-first · DS-013 denormalize place · DS-014 TIMESTAMPTZ uplift

## Schema amendments (S1 column alterations)
Migration 0003 in-place ALTERs the 4 existing `created_at` columns from `TIMESTAMP` to `TIMESTAMPTZ`. Existing values are interpreted as UTC during the ALTER. Closes TD-007.
- `tbl_supplier_master.created_at` → TIMESTAMPTZ
- `tbl_staff_master.created_at` → TIMESTAMPTZ
- `tbl_dealer_master.created_at` → TIMESTAMPTZ
- `tbl_trading_design_master.created_at` → TIMESTAMPTZ

## New entities

### Transaction tables (M-002)

| Table | FK parents | Key fields | Special |
|-------|-----------|------------|---------|
| `tbl_inward_header` | supplier, staff | purchase_date, supplier_id, place (snap), entered_by_id | place denormalized per DS-013 |
| `tbl_inward_line` | inward_header, design, grade | header_id, design_id, grade_id, nos | CHECK(nos > 0); CASCADE on header delete |
| `tbl_sales_header` | dealer, staff×2 | sales_date, dealer_id, place (snap), loading_staff_id, verified_by_id | 2 staff FKs; place per DS-013 |
| `tbl_sales_line` | sales_header, design, grade | header_id, design_id, grade_id, nos | CHECK(nos > 0); CASCADE |
| `tbl_adjustment_header` | design, staff | stock_date, entry_date, design_id, entered_by_id | Design on the HEADER (1 design per AC-034); CHECK(stock_date ≤ entry_date) for ERR-010 |
| `tbl_adjustment_line` | adjustment_header, grade | header_id, grade_id, software_cb, physical_cb, difference | physical_cb ≥ 0 per AC-037; software_cb and difference persisted, not GENERATED |

### Stock ledger (M-003)

| Table | FK parents | Key fields | Special |
|-------|-----------|------------|---------|
| `tbl_stock_ledger` | design, grade | ledger_id, design_id, grade_id, txn_date, source_type, source_header_id?, source_line_id?, delta, running_balance, created_at | source_type ∈ {inward, sale, adjustment}; one composite index `ix_stock_ledger_dgt ON (design_id, grade_id, txn_date DESC, ledger_id DESC)` serves all 3 query patterns: closing-balance as-of-date lookup, SELECT FOR UPDATE on latest row, forward-recompute window scan |

## Constraint summary

| Constraint | Source AC | Layer |
|------------|-----------|-------|
| `CHECK (nos > 0)` on 3 line tables | AC-024 / AC-032 | DB + Pydantic |
| `CHECK (physical_cb >= 0)` on adjustment_line | AC-037 | DB + Pydantic |
| `CHECK (stock_date <= entry_date)` on adjustment_header | AC-035 / ERR-010 | DB + Pydantic model_validator |
| `CHECK (source_type IN ('inward','sale','adjustment'))` on stock_ledger | M-003 invariant | DB |
| FKs all `ON DELETE RESTRICT` for master refs | DS-008 soft-delete only | DB |
| FKs `ON DELETE CASCADE` for line→header | structural — header is the aggregate root | DB |

## Indexes designed for known query patterns

| Index | Supports |
|-------|----------|
| `ix_stock_ledger_dgt` (composite descending) | closing_balance(date) LIMIT 1 · SELECT FOR UPDATE on latest row · rows_after window |
| `ix_inward_header_purchase_date` | S3 Dashboard date filter |
| `ix_sales_header_sales_date` | S3 Sales Report date filter + Dashboard |
| `ix_sales_header_dealer` | S3 Sales Report dealer filter (AC-046) |
| `ix_sales_line_dgd` (design_id, grade_id, header_id) | S3 Consolidation GROUP BY |
| `ix_inward_line_dgd` | parallel of sales_line_dgd for inward-side reports |
| `ix_inward_line_header`, `ix_sales_line_header`, `ix_adjustment_line_header` | header-detail fetch |
| `ix_adjustment_header_design_stock_date` | re-reading recent adjustments for a (design, stock_date) pair |

## Completeness
- ✓ Every LLD model has a schema entity (7/7)
- ✓ Every schema entity has an LLD model owner (7/7)
- ✓ Every constraint is declared at the DB level AND its application-layer enforcement is mapped to an AC

## Migration plan
`0003_transaction_and_ledger_tables.py` — `down_revision = "0002_master_tables"`:
1. ALTER 4 S1 `created_at` columns to TIMESTAMPTZ (DS-014)
2. CREATE 3 header tables (parents)
3. CREATE 3 line tables (FK children)
4. CREATE `tbl_stock_ledger`
5. CREATE all indexes

Downgrade: reverse order; drop indexes → drop tables → revert TIMESTAMPTZ to TIMESTAMP on the 4 S1 columns.

## Next step
→ `/ases-test-spec S2` — turn the 21 ACs (AC-020..AC-040) into concrete test specs with explicit inputs, expected outputs, and frameworks.
