# Changelog — Jayanth Trading Tiles System

All notable changes per sprint will land here, written by `/ases-release`.

## Sprint S2 — 2026-06-23
**Goal:** Transaction Forms + Stock Ledger — Inward, Sales, and Adjustment forms with grade-row auto-population, atomic header+lines+ledger writes, row-level locking on (design_id, grade_id), and basic ledger read API.
**Verdict:** SHIP

### Shipped
- **F-007 Inward Entry** (AC-020..AC-027) — date-bounded form (today−7..today), supplier+staff active checks, place auto-fill (DS-013 snapshot), active-pair grade rows, strip-blank-lines (RULE-017), ≥1 valid line requirement, atomic ledger write per line via `domain.stock.apply_inward`
- **F-008 Sales Entry** (AC-028..AC-033) — same date window, dealer+place snapshot, **both** loading_staff and verified_by required, mirror line-validation, ledger Δ=−nos via `domain.stock.apply_sale`
- **F-009 Stock Adjustment** (AC-034..AC-040) — single design per header, `stock_date ≤ entry_date` enforced via Pydantic + DB CHECK, software_cb auto-populated per grade via `GET /designs/{id}/grades-with-cb`, signed difference (no abs), atomic ledger write with zero-diff audit-only optimization, ERR-012 banner on empty active grades

### Verified
- **112 / 112 backend tests pass** (S1 regression 46 + S2 backend 43 + system 12 + fixtures 11)
- **4 / 4 integration scenarios pass** (IS-005..IS-008 — incl. back-date forward-recompute)
- **4 / 4 system tests pass** (perf p95=4.4ms vs 100ms budget; boundary AC-021 exact; security defense-in-depth; concurrency 2-session)
- **5 / 13 frontend tests pass** + 7 deferred (Radix-Select jsdom — TD-010)
- **21 / 21 UAT ACs accepted**

### Architectural decisions added
- **DS-013** — Denormalize `place` onto Inward/Sales transaction headers (snapshot at save; historical immutability)
- **DS-014** — TIMESTAMPTZ upgrade on TimestampMixin + 4 S1 columns ALTERed in migration 0003 (closes TD-007)

### Tech Debt
- **TD-007** **closed** by DS-014 (TIMESTAMPTZ uplift)
- **TD-009** **closed** by /ases-test-impl (6 frontend zod-only TCs implemented)
- **TD-011** **discovered and closed in-step** during /ases-system-test S2 ST-007: PG `SELECT FOR UPDATE LIMIT 1 ORDER BY ...` doesn't re-resolve LIMIT after waiting on a row lock — broken serialization for the "lock the latest" pattern. Fix: `pg_advisory_xact_lock(design_id, grade_id)` added before `FOR UPDATE` in `domain.stock._apply`. 4-line addition; iteration 2 verified PASS.
- **TD-008** (open, V2) — First-row insert race (theoretical, once per (design, grade) lifetime). Likely subsumed by TD-011's advisory-lock fix since the lock acquires even when no row exists. Re-verify in S3.
- **TD-010** (open, S3 or V2) — 7 frontend tests (TC-092/093/095/097/099/101/102) can't exercise Radix UI Select/Popover in jsdom. Backend API tests cover the same ACs. Options: jest mock @radix-ui/react-select with native select shim, or move to Playwright/Cypress E2E.

### Deferred / Carry-Forward
- **CF-001 (W5)** — still pending from S1; PO bring-up of long-lived PG. Phase 3 verification used ephemeral testcontainers per IS-002 pattern.

### Highlights
- **16 / 16 backend tasks CLEAN on iteration 1** — first sprint with zero-iteration backend dev
- **TD-007 closed** + **TD-011 discovered + closed in-step** — DS-002 concurrency invariant now empirically verified, not just spec-text
- Write-path performance **23× under budget** — ample headroom for S3 dashboard read-path
- **DS-002 spec text refinement recommended for S3** to mandate advisory-lock-first layered pattern (FA-S2-002/003)

### Commit
`68a675e` on `develop` (204 files, +15300 / −36).

---

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
