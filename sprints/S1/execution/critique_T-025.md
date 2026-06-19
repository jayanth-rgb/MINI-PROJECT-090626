# Critique — T-025 Seed Master Data

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN (runtime apply deferred — same W5 as T-024)

## Files audited
- `backend/scripts/seed_master_data.py` (148 lines)
- `backend/scripts/__init__.py` (1 line — package marker, preserved)

## Decisions referenced (read first)
- **DS-009** ORM is source-of-truth — seed script writes through ORM models, not raw SQL

## Lens 1 — Spec
LLD `files[31]` parity (7 functions):
- `seed_suppliers`, `seed_staff`, `seed_dealers`, `seed_grades`, `seed_designs`, `seed_design_grade_map`, `main` ✓
- All seeders take `session: Session` and return `None` ✓
- `main()` opens `SessionLocal`, runs the 6 seeders in dependency order, commits once, closes ✓
- CLI entry: `if __name__ == "__main__": main()` enables `python -m scripts.seed_master_data` ✓

Plan.md pseudo-code matches verbatim (module-level lists, per-seeder existence-check-then-add pattern, `session.flush()` in `seed_design_grade_map` before resolving FKs).

## Lens 2 — Contract
Imports vs `depends_on = ["T-002", "T-004", "T-024"]`:
- T-002 → `SessionLocal` from `session.py` ✓ (confirmed at session.py:16, `autoflush=False, autocommit=False, expire_on_commit=False`)
- T-004 → all 6 ORM models from `master.py` ✓
- T-024 → schema produced by `0002_master_tables.py` migration (runtime dependency; file artifact present, apply deferred per W5)
- `from sqlalchemy import select` + `from sqlalchemy.orm import Session` for type+queries ✓

Exports vs LLD `interfaces.exports`: `main` + the 6 `seed_*` functions all defined at module level ✓.

## Lens 3 — Test (6/6 expected outputs verified)
Per `expected_output` exact-match check against script constants:

| TC | AC | Expected | Implementation | Match |
|----|----|----------|----------------|-------|
| TC-007 | AC-003 | 3 suppliers: (Manjunatha, Mallur), (Dinnesh Reddy, Mallur), (Antony Tiles, Kerala) | `SUPPLIERS` list | ✓ exact |
| TC-011 | AC-006 | 9 staff: Chandran, Jayapal, Ramachandraiah, Sujatha, Ramya, Vijay, Sajil, Ashu, Amaresh | `STAFF` list | ✓ exact (order preserved) |
| TC-015 | AC-009 | 3 dealers: Raj Hardwares/Dindivanam, Tiles Mart/Attibelle, Shanmugam & Co/Coimbatore | `DEALERS` list | ✓ exact |
| TC-016 | AC-010 | 9 grade codes: 1, 2, 2A, 4, 5, 6, 1OB, OB, DIM | `GRADE_CODES` list | ✓ exact |
| TC-022 | AC-014 | 3 designs: 16X10/16X10 Ridges, 12X8/12X8 Ridges, 11X7/11X7 Ridges | `DESIGNS` list | ✓ exact |
| TC-030 | AC-018 | 6 pairs: 16X10 Ridges {1,2}, 12X8 Ridges {1,OB}, 11X7 Ridges {1,2} | `DESIGN_GRADE_PAIRS` | ✓ exact (6 tuples in expected order) |

**Idempotency** (every TC has `run_count: 2`, expects same row count): each seeder issues an existence SELECT on the natural key before `add()`. `autoflush=False` means the SELECT sees only committed rows — on first run, table is empty so all inserts proceed; on second run, all 33 rows are committed so all SELECTs find them and no `add()` fires. ✓

## Lens 4 — Security
- All inserts via ORM `add(Model(**row))` — parameterized through SQLAlchemy ✓
- No user input; all seed values are hardcoded business data from PRD samples ✓
- No secrets in seed content; no logging of sensitive data ✓
- `SessionLocal` is used directly (not `get_db`); appropriate for a CLI script — `get_db` is the FastAPI request-scoped generator and would auto-commit on a yielded session ✓
- Single transaction per `main()` invocation — all-or-nothing semantics; a mid-script error rolls back the implicit transaction on `session.close()` without commit ✓

## Lens 5 — Structural
- Reachable via `python -m scripts.seed_master_data` — `scripts/__init__.py` makes it a package; `prepend_sys_path = .` in `alembic.ini` (or running from `backend/`) resolves the `src.*` imports ✓
- Not imported by application code — operational script only ✓
- Pre-existing `__init__.py` comment retained: package-resolvable + small developer breadcrumb. Output_files declaration satisfied (file re-written with same content) ✓

## Runtime apply note (carry-forward W5)
The plan's `success_criteria.manual` (`python -m scripts.seed_master_data` inserts 33 rows; re-run inserts 0) requires:
1. PO sets `backend/.env` (`DATABASE_URL=...`)
2. `docker-compose up -d db`
3. `cd backend && alembic upgrade head` (applies T-024 migration)
4. `python -m scripts.seed_master_data` (this task) → 33 rows
5. Re-run → 0 new rows

Steps 1-3 are the W5 PO action already tracked in `context.open_issues`. Step 4-5 verification will validate this task's runtime DoD.

## Verdict
**CLEAN** — all 6 seeder constants exactly match the 6 TC `expected_output` blocks; idempotency invariant holds via per-row natural-key SELECT; single-transaction `main()` provides all-or-nothing semantics. Runtime verification is gated on the same W5 PO action as T-024.
