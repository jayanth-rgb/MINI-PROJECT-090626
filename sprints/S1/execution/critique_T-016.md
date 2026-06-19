# Critique — T-016 FastAPI Dependency Providers

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/dependencies.py` (35 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — presentation factory only constructs application services; no DB or domain logic
- **DS-012** generic BaseRepository — service constructors handle repo wiring internally; factory body is one line each

## Lens 1 — Spec
LLD `files[14].functions` parity (6 factories):
- `get_supplier_service(db: Session = Depends(get_db)) -> SupplierService` ✓
- `get_staff_service(...)` ✓
- `get_dealer_service(...)` ✓
- `get_grade_service(...)` ✓
- `get_design_service(...)` ✓
- `get_design_grade_map_service(...)` ✓

Plan.md pseudo-code matches verbatim (import order alphabetized; semantically equivalent — no functional change).

## Lens 2 — Contract
Imports vs `depends_on = ["T-002", "T-010..T-015"]`:
- T-002 → `get_db` from `src.infrastructure.db.session` ✓
- T-010..T-015 → all 6 service classes imported from their respective modules ✓
- `fastapi.Depends`, `sqlalchemy.orm.Session` for type+wiring ✓

Exports vs LLD `interfaces.exports`:
- 6 named functions exported at module level — all 6 LLD exports satisfied ✓
- No stray symbols beyond the spec ✓

Each service constructor accepts `Session` as its sole positional arg — verified against `supplier_service.py:8`, `design_service.py:8`, `design_grade_map_service.py:18`, etc. ✓

## Lens 3 — Test
- `test_case_refs = []` — no direct test cases. Exercised transitively by integration TC-033..TC-038 (router-level). DoD: 6 callables exist and each takes `Session = Depends(get_db)`. Both conditions hold by inspection. ✓

## Lens 4 — Security
- Pure dependency injection wiring; no user input, no secrets, no I/O ✓
- Each provider is a fresh factory — no module-level shared `Session` (avoids cross-request contamination) ✓
- `get_db` itself (T-002) manages the transactional boundary with rollback-on-exception; factories do not catch or swallow errors ✓

## Lens 5 — Structural
- Consumed by 6 router files (T-017..T-022) — each imports the matching `get_*_service` factory ✓
- `dependencies.py` itself imported by routers, indirectly mounted via `main.py` (T-023) ✓
- No orphaned imports or dead exports ✓

## Verdict
**CLEAN** — pure wiring, exact signature match, all 6 services correctly composed with `Session = Depends(get_db)`. Proceed.
