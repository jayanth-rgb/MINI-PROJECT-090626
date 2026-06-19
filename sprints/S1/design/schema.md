# Sprint S1 — Data Schema

**Produced by:** `/ases-schema S1`
**Sprint:** S1 — Master Data Foundation
**HLD modules in scope:** M-001 (Master Data Management), M-007 (Persistence & Migrations)
**PRD features in scope:** F-001 … F-006
**Companion JSON:** [schema.json](./schema.json)

---

## 1. Scope & Source-of-Truth

Sprint 1 establishes the persistent foundation for the entire system: six master tables that every later sprint will JOIN against. There is no transactional data in S1 — tables for Inward / Sales / Adjustments / Stock Ledger arrive in S2/S3.

**ADR alignment:**

| ADR | Effect on this schema |
|-----|-----------------------|
| [DS-001](../../../.ases/decisions.md) — Stack | PostgreSQL 16 + SQLAlchemy 2.x + Alembic; types use PostgreSQL semantics (`BIGSERIAL`, `TEXT`, `TIMESTAMPTZ`). |
| [DS-007](../../../.ases/decisions.md) — Layered architecture | ORM lives in `backend/src/infrastructure/db/models/master.py`; schema is enforced from the infrastructure layer only. |
| [DS-008](../../../.ases/decisions.md) — Soft delete only | Every entity carries `is_active BOOLEAN NOT NULL DEFAULT TRUE`. No hard-delete primitives anywhere. |
| [DS-009](../../../.ases/decisions.md) — Alembic autogenerate | Schema lives in ORM; the migration `0002_master_tables.py` is regenerated, not hand-written. |
| [DS-012](../../../.ases/decisions.md) — Generic repository | Schema shape is uniform across entities so `BaseRepository[TModel]` works for all six. |

---

## 2. Entities at a Glance

| # | Table | HLD module | Feature | PK | created_at? | Soft-delete? | Special constraints |
|---|-------|-----------|---------|----|-------------|-------------|---------------------|
| 1 | `tbl_supplier_master`       | M-001 | F-001 | `supplier_id` BIGSERIAL | ✅ | ✅ | — |
| 2 | `tbl_staff_master`          | M-001 | F-002 | `staff_id` BIGSERIAL    | ✅ | ✅ | — |
| 3 | `tbl_dealer_master`         | M-001 | F-003 | `dealer_id` BIGSERIAL   | ✅ | ✅ | — |
| 4 | `tbl_grade_master`          | M-001 | F-004 | `grade_id` BIGSERIAL    | ❌ | ✅ | `UNIQUE(grade_code)` (AC-011) |
| 5 | `tbl_trading_design_master` | M-001 | F-005 | `design_id` BIGSERIAL   | ✅ | ✅ | — |
| 6 | `tbl_design_grade_map`      | M-001 | F-006 | `map_id` BIGSERIAL      | ❌ | ✅ | `UNIQUE(design_id, grade_id)` (AC-016) + 2 FKs |

> **Why no `created_at` on grade and design-grade-map?**
> Both are canonical reference rows. Grade is seeded once at install per AC-010 and rarely edited. `tbl_design_grade_map` is a junction table; auditing belongs on the transactions that reference it (S2). The LLD frontend type definitions also omit `created_at` for both — keeping the schema in lock-step.

---

## 3. Entity Detail

### 3.1 `tbl_supplier_master` — F-001, M-001

```sql
CREATE TABLE tbl_supplier_master (
  supplier_id     BIGSERIAL    PRIMARY KEY,
  supplier_name   TEXT         NOT NULL,
  place           TEXT         NOT NULL,
  is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_supplier_master_is_active ON tbl_supplier_master (is_active);
```

| Field | Type | Notes |
|-------|------|-------|
| `supplier_id`   | BIGSERIAL    | Surrogate PK |
| `supplier_name` | TEXT NOT NULL | Required (AC-001). Pydantic `min_length=1`. |
| `place`         | TEXT NOT NULL | Required (AC-001). Auto-populated read-only into Inward form on supplier select (AC-022). |
| `is_active`     | BOOLEAN NOT NULL DEFAULT TRUE | Soft-delete (DS-008, AC-002). |
| `created_at`    | TIMESTAMPTZ NOT NULL DEFAULT now() | Insert-time stamp. |

**Acceptance criteria covered:** AC-001, AC-002, AC-003.

---

### 3.2 `tbl_staff_master` — F-002, M-001

```sql
CREATE TABLE tbl_staff_master (
  staff_id      BIGSERIAL    PRIMARY KEY,
  staff_name    TEXT         NOT NULL,
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_staff_master_is_active ON tbl_staff_master (is_active);
```

**Acceptance criteria covered:** AC-004, AC-005, AC-006.

Active staff feed three dropdowns in S2 forms (`entered_by` on Inward, `loading_staff_id` + `verified_by_id` on Sales) — `ix_staff_master_is_active` is sized for that read path.

---

### 3.3 `tbl_dealer_master` — F-003, M-001

```sql
CREATE TABLE tbl_dealer_master (
  dealer_id     BIGSERIAL    PRIMARY KEY,
  dealer_name   TEXT         NOT NULL,
  place         TEXT         NOT NULL,
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_dealer_master_is_active ON tbl_dealer_master (is_active);
```

**Acceptance criteria covered:** AC-007, AC-008, AC-009.

Powers the Sales form dealer dropdown (AC-029 — `place` auto-populates read-only) and the Sales Report dealer / place filters in S3.

---

### 3.4 `tbl_grade_master` — F-004, M-001

```sql
CREATE TABLE tbl_grade_master (
  grade_id     BIGSERIAL  PRIMARY KEY,
  grade_code   TEXT       NOT NULL,
  is_active    BOOLEAN    NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_grade_master_grade_code UNIQUE (grade_code)
);
CREATE INDEX ix_grade_master_is_active ON tbl_grade_master (is_active);
```

| Field | Type | Notes |
|-------|------|-------|
| `grade_id`   | BIGSERIAL    | Surrogate PK |
| `grade_code` | TEXT NOT NULL UNIQUE | AC-011 — DB-enforced UNIQUE in addition to the service-layer pre-check in `GradeService.create_grade`. |
| `is_active`  | BOOLEAN NOT NULL DEFAULT TRUE | AC-012 soft-delete. |

**Acceptance criteria covered:** AC-010, AC-011, AC-012.

**Seed values (exactly 9 per AC-010):** `1`, `2`, `2A`, `4`, `5`, `6`, `1OB`, `OB`, `DIM`.

The `UNIQUE` constraint surfaces as `IntegrityError` from SQLAlchemy → HTTP 409 via the `register_error_handlers` mapper, and is also pre-checked by `repo.get_by_code` so the service can raise `ConflictError` with a meaningful message.

---

### 3.5 `tbl_trading_design_master` — F-005, M-001

```sql
CREATE TABLE tbl_trading_design_master (
  design_id     BIGSERIAL    PRIMARY KEY,
  size          TEXT         NOT NULL,
  design_name   TEXT         NOT NULL,
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_trading_design_master_is_active ON tbl_trading_design_master (is_active);
```

**Acceptance criteria covered:** AC-013, AC-014, AC-015.

Explicit PRD constraint: this is the *trading* design catalogue, deliberately separate from any future manufactured-tile catalogue.

---

### 3.6 `tbl_design_grade_map` — F-006, M-001 (the junction table)

```sql
CREATE TABLE tbl_design_grade_map (
  map_id      BIGSERIAL  PRIMARY KEY,
  design_id   BIGINT     NOT NULL REFERENCES tbl_trading_design_master(design_id) ON DELETE RESTRICT,
  grade_id    BIGINT     NOT NULL REFERENCES tbl_grade_master(grade_id)             ON DELETE RESTRICT,
  is_active   BOOLEAN    NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_design_grade_map_design_grade UNIQUE (design_id, grade_id)
);
CREATE INDEX ix_design_grade_map_design_id  ON tbl_design_grade_map (design_id);
CREATE INDEX ix_design_grade_map_is_active  ON tbl_design_grade_map (is_active);
```

| Constraint | Source | Behaviour |
|------------|--------|-----------|
| `UNIQUE (design_id, grade_id)` | AC-016 | Prevents duplicate mappings; surfaces as HTTP 409. |
| `FK design_id → tbl_trading_design_master` | DS-008 invariant | `ON DELETE RESTRICT` is belt-and-braces — V1 has no hard delete anywhere. |
| `FK grade_id → tbl_grade_master` | DS-008 invariant | Same. |

**Acceptance criteria covered:** AC-016, AC-017, AC-018, AC-019.

**Seed values (AC-018) — 6 mappings:**
| Design | Grades |
|--------|--------|
| 16X10 Ridges | 1, 2 |
| 12X8 Ridges  | 1, OB |
| 11X7 Ridges  | 1, 2 |

---

## 4. Index Strategy & Query Patterns

Every index in this schema exists to serve a named query pattern. Nothing speculative.

| Index | Serves query | AC / DF |
|-------|--------------|---------|
| `ix_supplier_master_is_active` | `SELECT … WHERE is_active = TRUE` (active dropdown) | F-001 |
| `ix_staff_master_is_active`    | Active staff feed for S2 forms | F-002 / DF-007 staff dropdowns |
| `ix_dealer_master_is_active`   | Active dealer feed for Sales form + Sales Report filter | F-003 |
| `uq_grade_master_grade_code`   | Pre-insert uniqueness check + AC-011 enforcement | AC-011 |
| `ix_grade_master_is_active`    | Active grade JOIN filter for design-grade reads | F-004 |
| `ix_trading_design_master_is_active` | Active design dropdown for transaction forms | F-005 |
| `uq_design_grade_map_design_grade`  | Pre-insert pair uniqueness + AC-016 enforcement | AC-016 |
| `ix_design_grade_map_design_id`     | `GET /designs/{id}/grades` (DF-006 / AC-019) | DF-006 |
| `ix_design_grade_map_is_active`     | Admin list active mappings | AC-017 |

### 4.1 Named Query Patterns

- **QP-001** — Active masters dropdown:
  `SELECT * FROM tbl_<entity>_master WHERE is_active = TRUE ORDER BY <name_col> ASC`
- **QP-002** — Grade-code uniqueness pre-check:
  `SELECT * FROM tbl_grade_master WHERE grade_code = :code`
- **QP-003** — Active grades for a design (HLD DF-006, AC-019):
  ```sql
  SELECT m.grade_id, g.grade_code
    FROM tbl_design_grade_map m
    JOIN tbl_grade_master g ON g.grade_id = m.grade_id
   WHERE m.design_id = :did
     AND m.is_active = TRUE
     AND g.is_active = TRUE;
  ```
- **QP-004** — Design-grade pair uniqueness pre-check:
  `SELECT * FROM tbl_design_grade_map WHERE design_id = :did AND grade_id = :gid`

---

## 5. Relationships

```
tbl_trading_design_master 1 ─┐
                             ├─< tbl_design_grade_map >─ many ─ tbl_grade_master
tbl_grade_master          1 ─┘

tbl_supplier_master       (no relationships in S1 — referenced from S2 tbl_inward_header)
tbl_staff_master          (no relationships in S1 — referenced from S2 inward/sales headers)
tbl_dealer_master         (no relationships in S1 — referenced from S2 tbl_sales_header)
```

No implicit FKs. All cross-entity links are explicit FOREIGN KEY constraints.

---

## 6. Migrations

| Revision | File | Notes |
|----------|------|-------|
| `0001_baseline` | (existing placeholder from `/ases-scaffold`) | No DDL; anchor only. |
| `0002_master_tables` | `backend/db/migrations/versions/0002_master_tables.py` | **This sprint.** Creates all 6 tables, indices, UNIQUE constraints, FKs. |

**Generator workflow (per DS-009):**
1. Commit the ORM model file.
2. Run `alembic revision --autogenerate -m "master tables"`.
3. Reviewer diffs generated DDL against §3 of this document.
4. Hand-add `op.create_index` lines for any missing `is_active` / `design_id` indices (autogenerate is known to miss some non-PK / non-FK indices).
5. Verify `downgrade()` drops in reverse dependency order: `tbl_design_grade_map` first.

---

## 7. Completeness Check (`/ases-sprint-gate` inputs)

| Check | Status |
|-------|--------|
| Every LLD persistence model has a schema entity | ✅ 6 / 6 |
| Every entity has an `hld_module` reference | ✅ |
| Every entity links to a PRD feature (`feature_ref`) | ✅ |
| Every relationship is an explicit FK — no implied | ✅ |
| Soft-delete invariant uniform across all entities | ✅ |
| Every index justified by a query pattern | ✅ |
| Every constraint maps to an acceptance criterion | ✅ |
| `created_at` omissions documented | ✅ (§2 / per-entity notes) |
| No entity from prior sprint requires schema change | ✅ N/A — S1 is the first sprint |

---

## 8. What's NOT in this schema (intentionally deferred)

| Entity | Sprint | Reason |
|--------|--------|--------|
| `tbl_inward_header`, `tbl_inward_lines` | S2 | F-007 — Inward form |
| `tbl_sales_header`, `tbl_sales_lines`   | S2 | F-008 — Sales form |
| `tbl_adjustment_header`, `tbl_adjustment_lines` | S2 | F-009 — Adjustment form |
| `tbl_stock_ledger` | S2/S3 | F-010, F-012 — Stock dashboard & monthly carry-forward (DS-002, DS-003, DS-004) |

These are referenced by the LLD only as outbound dependencies (`supplier_id`, `staff_id`, `dealer_id` will be FK targets) — that contract is already preserved in this schema by the surrogate `BIGSERIAL` PKs.

---

## 9. Next Step

→ **`/ases-test-spec S1`** — generate test case specifications from PRD acceptance criteria + LLD interfaces, scoped to F-001…F-006. Every test case must link to an `ac_ref` listed in this schema.
