# Critique — T-023 FastAPI App Factory

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/main.py` (45 lines)

## Decisions referenced (read first)
- **DS-005** V1 no auth — confirmed no auth middleware added; only CORS
- **DS-006** separate backend/frontend Docker images talking via HTTP — CORS configured for cross-origin frontend calls
- **DS-010** API versioning — all 6 master routers mounted under `/api/v1`

## Lens 1 — Spec
LLD `files[22]` parity:
- `create_app() -> FastAPI` ✓ (title `"Jayanth Trading Tiles API"`, version `"1.0.0"`)
- Module-level `app = create_app()` for uvicorn ✓
- CORS middleware reading `settings.api_cors_origins` ✓
- `register_error_handlers(app)` ✓
- `include_router` for all 6 master routers under `prefix="/api/v1"` ✓
- `GET /health` → `{"status": "ok"}` unversioned operational endpoint ✓

Plan.md pseudo-code matches verbatim (router import order normalized alphabetically; semantically identical).

## Lens 2 — Contract
- T-001 → `get_settings` ✓ — `Settings.api_cors_origins: list[str]` confirmed at `config.py:10`
- T-008 → `register_error_handlers` ✓
- T-017..T-022 → all 6 router modules imported and mounted ✓
- Exports `create_app`, `app` per LLD `interfaces.exports` ✓
- All 8 declared `depends_on` (T-001, T-008, T-017..T-022) are exercised in the body ✓

## Lens 3 — Test
- `test_case_refs = []`. DoD verifiable:
  - `uvicorn src.main:app --reload` starts (module-level `app` exists) ✓
  - `curl /health` → `{"status":"ok"}` ✓
  - `/docs` lists all 6 master routers under `/api/v1` ✓
  - Integration TCs (TC-033..TC-038) all use this `app` via FastAPI `TestClient` — indirect coverage ✓

## Lens 4 — Security
- `allow_origins=settings.api_cors_origins` reads explicit list (NOT wildcard) ✓
- `allow_credentials=False` — explicitly disabled; combined with `allow_origins` whitelist, this is the safer posture ✓
- `allow_methods=["*"]` / `allow_headers=["*"]` — broad but gated by origin whitelist ✓
- Default `api_cors_origins: list[str] = []` in `config.py:10` means deny-by-default unless PO sets `API_CORS_ORIGINS` — safer than a permissive default ✓
- `/health` is intentionally unauthenticated (operational endpoint; standard for liveness probes) ✓
- DS-005 V1 no-auth limitation ADR-tracked — not a critique-blocking finding ✓
- No secrets logged, no exception leakage (error handlers from T-008 own the response surface) ✓

## Lens 5 — Structural
- `app` is the uvicorn ASGI entry point (`uvicorn src.main:app`) ✓
- All 6 routers (24 master CRUD routes + 1 nested DF-006 grades route + 4 design-grade-map admin routes = 29 endpoints) reachable under `/api/v1/<entity>` ✓
- `/health` reachable at `/health` (intentionally unversioned per plan) ✓
- Error handlers registered BEFORE routers — ensures they intercept exceptions raised inside route handlers ✓

## Verdict
**CLEAN** — app factory complete; CORS deny-by-default; 6 routers wired under `/api/v1`; `/health` exposed; error handlers wrap the surface. Sprint S1 backend wiring is now closed.
