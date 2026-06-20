# Changelog — Jayanth Trading Tiles System

All notable changes per sprint will land here, written by `/ases-release`.

## Sprint S1 — 2026-06-20
**Goal:** Data Foundation — 6 master tables, CRUD admin screens, soft-delete, seed data, PostgreSQL schema, Alembic baseline migration.
**Verdict:** SHIP

### Shipped
- **F-001 Supplier Master** (AC-001, AC-002, AC-003) — name+place CRUD, soft-delete, 3-row seed
- **F-002 Staff Master** (AC-004, AC-005, AC-006) — name CRUD, soft-delete, 9-row seed
- **F-003 Dealer Master** (AC-007, AC-008, AC-009) — name+place CRUD, soft-delete, 3-row seed
- **F-004 Grade Master** (AC-010, AC-011, AC-012) — UNIQUE grade_code, soft-delete, 9-code seed
- **F-005 Trading Design Master** (AC-013, AC-014, AC-015) — size+design_name CRUD, soft-delete, 3-row seed
- **F-006 Design-Grade Mapping** (AC-016, AC-017, AC-018, AC-019) — UNIQUE pair, soft-delete, 6-pair seed, DF-006 contract `GET /designs/{id}/grades`

### Verified
- 46 / 46 test cases pass (50 test runs incl. parametrized expansions)
- 4 / 4 cross-module integration scenarios (incl. alembic + seed against a real PG via testcontainers)
- 3 / 3 executed system tests; 2 explicitly deferred to S3 (PRD performance NFRs, stock-ledger race) with documented reasons
- 19 / 19 UAT ACs accepted by PO

### Tech Debt
- TD-005 (minor, S1): Migration 0002 hand-authored from ORM (PG env unavailable at dev time). IS-002 verifies equivalence; final `alembic check` deferred until W5 closes.
- TD-006 (minor, S1): Seed runtime verification deferred until W5 closes; static verification CLEAN.
- TD-007 (minor, S2): `TimestampMixin` emits TIMESTAMP not TIMESTAMPTZ; LLD prose says TIMESTAMPTZ. Plan: edit `base.py` + ship follow-up migration in S2.

### Deferred / Carry-Forward
- **W5** (PO action): bring up long-lived PG with `.env` + `docker-compose up -d db` + `alembic upgrade head` + `python -m scripts.seed_master_data`. Required for live UI walk-through; not blocking.

### New Risks (low severity)
- RI-001: TIMESTAMP vs TIMESTAMPTZ drift (TD-007 mitigation in S2)
- RI-002: Long-lived PG dev env not yet bootstrapped (W5)

### Commit
`571c601a0dd0acdee0c1ac27abf6f0f71884d85b` on `develop` (17 files, +968/-8).

---

## [Pre-S1] — 2026-06-09
- ASES project initialized
- Project Start phase complete: brief, PRD, HLD, roadmap, decisions (DS-001..DS-012)
- Scaffold delivered
