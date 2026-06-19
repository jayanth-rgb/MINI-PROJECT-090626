# Critique — T-019 Dealers Router

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/dealers.py` (41 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — pure delegation to `DealerService`
- **DS-008** soft delete — DELETE returns the deactivated `DealerRead`
- **DS-010** API versioning — `/dealers` prefix; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[18]` parity: 4 routes (list/create/update/delete). `APIRouter(prefix="/dealers", tags=["dealers"])` ✓. Plan.md pseudo-code matches verbatim.

## Lens 2 — Contract
- T-016 → `get_dealer_service` ✓
- T-012 (transitive) → `DealerService` type annotation ✓
- T-007 → `DealerCreate / DealerRead / DealerUpdate` ✓
- Exports `router` per LLD `interfaces.exports` ✓

## Lens 3 — Test
- `test_case_refs = []` for the router; service-layer coverage via TC-012/TC-014 already validated in T-012. DoD ("Same shape as suppliers router using Dealer schemas and DealerService") is satisfied — identical structure to `suppliers.py`/`staff.py` with `Dealer*` substitutions. ✓

## Lens 4 — Security
- Path param `dealer_id: int` auto-coerced + 422 on non-int ✓
- POST body bound to `DealerCreate` enforcing `dealer_name: min_length=1` and `place: min_length=1` (AC-007) ✓
- `response_model=DealerRead` strips ORM extras ✓
- No auth — DS-005 V1 limitation ADR-tracked ✓

## Lens 5 — Structural
- Mounted in `main.py` (T-023): `app.include_router(dealers.router, prefix="/api/v1")` ✓
- All 4 routes reachable ✓

## Verdict
**CLEAN** — mirror of suppliers router with Dealer types; soft DELETE returns row; no scope creep.
