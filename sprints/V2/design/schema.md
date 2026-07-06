# V2 Data Schema

**Sprint:** V2 · **Produced by:** `/ases-schema V2` · **Next:** `/ases-test-spec V2`

---

## Summary

| Category | Count |
|---|---|
| New tables | 5 |
| Modified tables | 0 |
| Read-only reused | 7 |
| Total entities | 12 |
| New indexes | 5 |
| Reused indexes | 8 |
| Modules | M-008, M-009, M-010, M-011 |
| Features | F-013, F-014, F-015, F-016, F-017, F-018, F-019 |
| Migration | `0004_v2_auth_pricing_tables` (down_revision: `0003_tx_ledger`) |

**Schema note:** V2 sprint_id deviates from the `^S\d+$` pattern in `schema.schema.json` (V1-only scope). Acknowledged in `lld.json`. Pattern will be relaxed to `^(S\d+|V\d+)$` at next schema meta-update.

---

## New Tables

### 1. `tbl_user_master` — M-008 (Auth & Authorization)

**Features:** F-013, F-014

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | SERIAL | NO | — | PK autoincrement |
| `username` | VARCHAR(100) | NO | — | UNIQUE. Login identifier |
| `password_hash` | VARCHAR(255) | NO | — | bcrypt via passlib (DS-018) |
| `role` | VARCHAR(20) | NO | — | CHECK IN ('STAFF','VERIFIER','SUPERVISOR') — DS-019 |
| `is_active` | BOOLEAN | NO | TRUE | Soft-delete (DS-008) |
| `created_at` | TIMESTAMPTZ | NO | NOW() | TimestampMixin (DS-014) |

**Constraints:** PRIMARY KEY(id), UNIQUE(username), CHECK(role IN (...))

**Indexes:**
- `ix_user_master_username ON (username)` — O(1) login lookup + get_current_user re-fetch on every authenticated request

**Design decisions:**
- **DS-018:** JWT HS256, 8h TTL, no refresh tokens. `is_active` re-checked on every request — deactivation effective on next API call.
- **DS-019:** role as VARCHAR CHECK (not Postgres ENUM) — avoids ALTER TYPE migration if V3 adds a 4th role.

---

### 2. `tbl_price_master` — M-011 (Pricing & Invoicing)

**Features:** F-017

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | SERIAL | NO | — | PK autoincrement |
| `design_id` | INTEGER | NO | — | FK → tbl_trading_design_master.id |
| `grade_id` | INTEGER | NO | — | FK → tbl_grade_master.id |
| `unit_price` | NUMERIC(10,2) | NO | — | CHECK >= 0. Zero is valid (placeholder) |
| `effective_from` | DATE | NO | — | Time-aware pricing (DS-022) |
| `is_active` | BOOLEAN | NO | TRUE | Soft-delete (DS-008) |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Audit trail |

**Constraints:** PRIMARY KEY(id), UNIQUE(design_id, grade_id, effective_from) — `uq_price_design_grade_effective`, FK(design_id), FK(grade_id), CHECK(unit_price >= 0)

**Indexes:**
- `uq_price_design_grade_effective UNIQUE ON (design_id, grade_id, effective_from)` — enforces uniqueness AND services `get_active_price` query: `WHERE design_id=X AND grade_id=G AND is_active=true AND effective_from <= today ORDER BY effective_from DESC LIMIT 1`

**Design decisions:**
- **DS-022:** effective-from price lookup gives time-aware pricing. Unit price snapshotted onto `tbl_invoice_line` at invoice creation — future edits to this row never retroact.
- **DS-008:** `is_active=false` retires a price row without deleting it; history preserved for audit.

---

### 3. `tbl_invoice_header` — M-011 (Pricing & Invoicing)

**Features:** F-018

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | SERIAL | NO | — | PK autoincrement |
| `invoice_number` | VARCHAR(30) | NO | — | UNIQUE. Deterministic: `INV-{YYYYMMDD}-{sales_header_id:05d}` |
| `sales_header_id` | INTEGER | NO | — | FK → tbl_sales_header.id. UNIQUE — one invoice per sale (DS-023) |
| `invoice_date` | DATE | NO | — | today() at creation time |
| `total_amount` | NUMERIC(12,2) | NO | — | Sum of line_totals. Immutable after creation |
| `status` | VARCHAR(10) | NO | 'PENDING' | CHECK IN ('PENDING','PARTIAL','PAID'). Updated on each payment |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Audit trail |

**Constraints:** PRIMARY KEY(id), UNIQUE(invoice_number), UNIQUE(sales_header_id), FK(sales_header_id), CHECK(status IN (...))

**Indexes:**
- `UNIQUE(invoice_number)` — implicit B-tree
- `UNIQUE(sales_header_id)` — implicit B-tree; enforces one-invoice-per-sale (DS-023)
- `ix_invoice_header_invoice_date ON (invoice_date)` — services GET /invoices date_from/date_to filter

**Design decisions:**
- **DS-023:** on-demand invoice creation by SUPERVISOR. `UNIQUE(sales_header_id)` is the authoritative double-invoicing guard.
- Status recomputed in memory by `compute_invoice_status` and written synchronously — no DB trigger.

---

### 4. `tbl_invoice_line` — M-011 (Pricing & Invoicing)

**Features:** F-018

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | SERIAL | NO | — | PK autoincrement |
| `invoice_header_id` | INTEGER | NO | — | FK → tbl_invoice_header.id |
| `sales_line_id` | INTEGER | NO | — | FK → tbl_sales_line.id. UNIQUE — one invoice line per sales line |
| `design_id` | INTEGER | NO | — | Snapshot of sales_line.design_id at creation. Immutable |
| `grade_id` | INTEGER | NO | — | Snapshot of sales_line.grade_id at creation. Immutable |
| `quantity` | INTEGER | NO | — | Snapshot of sales_line.nos at creation. Immutable |
| `unit_price` | NUMERIC(10,2) | NO | — | Price snapshot per DS-022. Zero if no active price configured |
| `line_total` | NUMERIC(12,2) | NO | — | quantity × unit_price (ROUND_HALF_UP, 2dp). Immutable |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Audit trail |

**Constraints:** PRIMARY KEY(id), UNIQUE(sales_line_id), FK(invoice_header_id), FK(sales_line_id)

**Indexes:**
- `UNIQUE(sales_line_id)` — implicit B-tree; prevents same sales_line on two invoices
- `ix_invoice_line_header ON (invoice_header_id)` — services joinedload of all lines for an invoice

**Design decisions:**
- **DS-022:** `unit_price` is a point-in-time snapshot — same immutability pattern as `tbl_inward_header.place` (DS-013). Post-creation price edits never silently change invoice totals.
- `design_id` and `grade_id` are snapshotted (not FK references) so invoice lines display correct identifiers even if a design or grade is later soft-deleted.

---

### 5. `tbl_payment` — M-011 (Pricing & Invoicing)

**Features:** F-019

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | SERIAL | NO | — | PK autoincrement |
| `invoice_header_id` | INTEGER | NO | — | FK → tbl_invoice_header.id |
| `payment_date` | DATE | NO | — | Date of payment as entered by SUPERVISOR |
| `amount` | NUMERIC(12,2) | NO | — | CHECK > 0. Overpayment guard in application layer (422) |
| `notes` | TEXT | YES | NULL | Optional (cheque number, bank ref etc.) |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Audit trail. Append-only table |

**Constraints:** PRIMARY KEY(id), FK(invoice_header_id), CHECK(amount > 0)

**Indexes:**
- `ix_payment_invoice_header ON (invoice_header_id)` — services joinedload of all payments for an invoice and payment sum in `record_payment`

**Design decisions:**
- Append-only table — no UPDATE or DELETE. Corrections via a new corrective entry. Preserves full payment audit trail.
- Overpayment guard (`cumulative_paid <= total_amount`) is in `InvoiceService.record_payment` (application layer). DB CHECK only enforces `amount > 0` — running total requires application knowledge.

---

## Read-Only Reused Tables

### First Time Read in V2

| Table | Original Sprint | Module(s) in V2 | Read-by |
|---|---|---|---|
| `tbl_inward_header` | S2 | M-009, M-010 | InwardReportService (consolidation + transactions queries) |
| `tbl_inward_line` | S2 | M-009, M-010 | InwardReportService (both queries) |
| `tbl_supplier_master` | S1 | M-009 | InwardReportService (JOIN for supplier_name projection) |

**Note on `tbl_inward_header.place`:** Denormalized snapshot per DS-013. InwardReportService reads `place` directly from the header row — not re-joined to `tbl_supplier_master` — so historical inward records show the place that was in effect at purchase time, even if the supplier record is later updated.

**Note on shared filter predicate (DS-017):** InwardReportService applies the same WHERE clause object to both consolidation and transactions queries. This guarantees `sum(transactions.nos) == sum(consolidation.total_nos)` by construction — asserted in service before return.

### Additional V2 Readers (already in S3 schema)

| Table | Original Sprint | New V2 Reader |
|---|---|---|
| `tbl_sales_header` | S2 | M-011 InvoiceService (existence check + date/dealer filters for listing) |
| `tbl_sales_line` | S2 | M-011 InvoiceService (fetch all lines by header_id for invoice line building) |
| `tbl_trading_design_master` | S1 | M-009 InwardReportService (design_name + size), M-011 PriceMasterModel lazy join |
| `tbl_grade_master` | S1 | M-009 InwardReportService (grade_code), M-011 PriceMasterModel lazy join |

---

## Migration Plan — `0004_v2_auth_pricing_tables`

**down_revision:** `0003_tx_ledger` (S3 had no migration)

**Upgrade order (FK-safe):**

1. CREATE TABLE `tbl_user_master` + `ix_user_master_username` — no FK deps
2. CREATE TABLE `tbl_price_master` + `uq_price_design_grade_effective` — deps: S1 masters
3. CREATE TABLE `tbl_invoice_header` + indexes — deps: S2 `tbl_sales_header`
4. CREATE TABLE `tbl_invoice_line` + indexes — deps: step 3 + S2 `tbl_sales_line`
5. CREATE TABLE `tbl_payment` + `ix_payment_invoice_header` — deps: step 3

**Downgrade order (strict reverse):**

1. DROP TABLE `tbl_payment`
2. DROP TABLE `tbl_invoice_line`
3. DROP TABLE `tbl_invoice_header`
4. DROP TABLE `tbl_price_master`
5. DROP TABLE `tbl_user_master`

**Post-migration:** Run `backend/scripts/seed_default_user.py` once after `alembic upgrade head`. Inserts default `admin` / `admin123` SUPERVISOR user. Idempotent — no-ops if admin already exists. Prints warning to change password on first login.

---

## Indexes in Play — V2

| Index | Sprint Added | Query Pattern |
|---|---|---|
| `ix_user_master_username` | V2 | Every login + every authenticated request (get_current_user) |
| `uq_price_design_grade_effective` | V2 | `get_active_price` lookup + create uniqueness pre-check |
| `ix_invoice_header_invoice_date` | V2 | GET /invoices date_from/date_to filter |
| `ix_invoice_line_header` | V2 | Eager-load invoice lines in get + create_with_lines |
| `ix_payment_invoice_header` | V2 | Eager-load payments in get + payment sum in record_payment |
| `ix_inward_header_purchase_date` | S2 | InwardReportService date_from/date_to filter |
| `ix_inward_header_supplier` | S2 | InwardReportService supplier_ids filter |
| `ix_inward_line_dgd` | S2 | InwardReportService GROUP BY + design_ids filter |
| `ix_inward_line_header` | S2 | InwardReportService JOIN inward_header |
| `ix_sales_header_sales_date` | S2 | InvoiceRepository.list date filter |
| `ix_sales_header_dealer` | S2 | InvoiceRepository.list dealer_id filter |
| `ix_sales_line_header` | S2 | InvoiceService fetch lines by header_id |
| `ix_sales_line_dgd` | S2 | (continued S3 Sales Report use; no new V2 direct use) |

---

## Completeness Check

| Check | Result |
|---|---|
| Every LLD persistence model has a schema entity | ✓ |
| Every schema entity has a corresponding LLD file | ✓ |
| No entity missing from LLD | ✓ |
| No LLD model missing from schema | ✓ |
| Decisions referenced exist in decisions.json (DS-005 through DS-023) | ✓ |
| Migration FK creation order validated | ✓ |
| Downgrade order is strict reverse of upgrade | ✓ |

---

*ASES V2 Schema · 5 new tables · 0 modified · 7 reused · Migration 0004 · `/ases-test-spec V2` next*
