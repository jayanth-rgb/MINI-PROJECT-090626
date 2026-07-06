# Critique — T-090 · `routers/pricing.py`

**Sprint:** V2 · **Module:** M-011 · **Verdict:** CLEAN

## Files reviewed
- `backend/src/presentation/api/routers/pricing.py`

## Decisions consulted
- **DS-007** (four-layer architecture) — router only imports from `application.services` + `presentation.schemas` + `presentation.api.dependencies` + `infrastructure.db.models.auth` (UserModel only used as type annotation for auth guard return). No router-to-repository shortcut.
- **DS-008** (soft-delete only) — task explicitly omits DELETE; deactivation is via PATCH with `is_active=False`. Correct.
- **DS-019** (RBAC via role enum + require_supervisor guard) — POST + PATCH use `Depends(require_supervisor)`; GET uses `Depends(get_current_user)`. Matches LLD contract.
- **DS-022** (unit_price snapshot at invoice creation) — enforced in InvoiceService, not this router. No leakage.

## Lens 1 — Spec
- 3 routes present: GET '', POST '' (201), PATCH '/{price_id}'.
- Router prefix `/prices`, tags `['pricing']` — matches LLD.
- Function signatures match LLD `interfaces.expects` and function specs.
- Pass.

## Lens 2 — Contract
- Imports resolve: `get_pricing_service`, `get_current_user`, `require_supervisor` all exported by `dependencies.py` (verified).
- `PricingService.list_prices / create_price / update_price` all exist with matching signatures (verified in `pricing_service.py`).
- Schemas `PriceMasterCreate / Read / Update` exist in `schemas/pricing.py`.
- `UserModel` imported from `infrastructure.db.models.auth` — matches user router pattern (used only as return-type annotation).
- Import prefix (`src.`) matches sibling routers auth.py and users.py — consistent.
- Pass.

## Lens 3 — Test
- Task declares no dedicated router TCs (`test_case_refs: []`). Router correctness is indirectly verified by TC-201..206 (service + invoice tests). Documented in `success_criteria.automated`.
- Manual criterion `len(router.routes) == 3` satisfied — 3 route decorators present.
- Pass.

## Lens 4 — Security
- Auth guards present on every route.
- No secrets in code; no dynamic string interpolation into SQL (delegates to service).
- POST body validated by Pydantic `PriceMasterCreate` (which enforces `unit_price >= 0` via `Field(ge=0)` — verified in schemas/pricing.py).
- PATCH body validated by `PriceMasterUpdate`; service applies `exclude_none=True` semantics safely.
- `price_id` is typed `int` on the path param — FastAPI coerces + rejects non-int automatically.
- Pass.

## Lens 5 — Structural
- Router is registered in `main.py` (`app.include_router(pricing_router)` at line 71) — reachable from FastAPI entry.
- No orphaned functions or dead imports in the file.
- Pass.

## Findings
None.

## Verdict
CLEAN — no fixes required.
