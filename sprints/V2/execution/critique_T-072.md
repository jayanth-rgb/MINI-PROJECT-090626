# Critique — T-072 `routers/auth.py` (iteration 3)

**Sprint:** V2 · **Module:** M-008 · **Iteration:** 3
**Prior:** iter1 FIX_REQUIRED (1 major, 1 minor) → iter2 ESCALATE (out-of-scope fix)
**Verdict:** ✅ **CLEAN**

## Summary

Iteration 3 re-audit after PO `go with T-072`. The router file is unchanged since iteration 1 (fix agent correctly refused to modify outside scope in iter2). The prior FIX_REQUIRED verdict is fully dissolved by two facts established outside T-072:

1. **T-092 iter3 CLEAN** mounted `auth_router` at `prefix="/api/v1"` (`main.py:59`) — the `/api/v1/auth/login` and `/api/v1/auth/me` paths that TC-208/209/210 target are now live. The iter1 `structural_lens` cross-task concern is resolved.
2. **TC-208/TC-209 body field is a semantic payload, not a wire-format directive** — the TC records `body: {username, password}` with **no `content_type`, no `headers`, no `Content-Type: application/json`**. Under ASES Hard Rule 2 (plan.json is authoritative), the wire format is dictated by:
   - `plan.json` — mandates `OAuth2PasswordRequestForm`
   - `DS-018` — mandates `OAuth2PasswordBearer` per RFC 6749 §4.3.2 (form-encoded token endpoint)
   - `dependencies.py:82` — `oauth2_scheme(tokenUrl='/api/v1/auth/login')` (Swagger will POST form-encoded here)

   Phase 3 test-impl (Sonnet) will encode TC-208/209 payloads via `httpx.post(..., data={...})` per the router's declared contract. LLD line 236's `data: LoginRequest` is documentation drift and is corrected in the next LLD refresh.

Counts: **0 critical · 0 major · 0 minor · 1 documentation drift to log at sprint-close.**

## Resolution Ledger

| ID | Prior | Status | Rationale |
|---|---|---|---|
| F-T072-01 | major (test) | ✅ RESOLVED_BY_REINTERPRETATION | TC `body` is semantic payload; wire format is form-encoded per plan.json + DS-018 + RFC 6749. Router is faithful to plan.json (prior critic's own `spec_lens` confirmed this). |
| F-T072-02 | minor (spec) | ✅ NO_CHANGE_NEEDED | Self-classified as doc nit. `src.`-prefixed imports match all other V2 routers + `main.py`. |
| iter1 `structural_lens` cross-task note | — | ✅ RESOLVED | T-092 iter3 mounted `auth_router` at `/api/v1`. |

## Regression Checks

- ✅ **prefix & tags** — [auth.py:9](backend/src/presentation/api/routers/auth.py#L9) `APIRouter(prefix='/auth', tags=['auth'])`.
- ✅ **login endpoint open** — [auth.py:12-14](backend/src/presentation/api/routers/auth.py#L12-L14) no `Depends(get_current_user)`, no router-level `dependencies=[]`. DS-018 compliant.
- ✅ **login form body** — [auth.py:14](backend/src/presentation/api/routers/auth.py#L14) `OAuth2PasswordRequestForm = Depends()` — RFC 6749 §4.3.2 compliant.
- ✅ **/me route-level auth** — [auth.py:30](backend/src/presentation/api/routers/auth.py#L30) `Depends(get_current_user)`; DB re-fetch enforces DS-018 immediate deactivation.
- ✅ **response models** — `TokenResponse` on `/login`, `UserRead` on `/me`; `password_hash` never exposed.
- ✅ **AuthService 401 semantics** — [auth_service.py:26-54](backend/src/application/services/auth_service.py#L26-L54) raises 401 on missing user, wrong password, and inactive user. TC-209 (wrong pw → 401) satisfied.

## PO Action (non-blocking)

At `/ases-sprint-close V2`, log **DS-024**:

> V2 auth login wire format is OAuth2 form-encoded (`application/x-www-form-urlencoded`) per `plan.json` + `DS-018` + RFC 6749 §4.3.2. TC-208/TC-209 `body` field is a semantic payload description; Phase 3 test-impl will encode via `httpx data=`. LLD line 236 (`data: LoginRequest`) is documentation drift and will be corrected in the next LLD refresh.

## Next Action

- Set T-072 → `status=complete`, `critique_verdict=CLEAN`, `iteration_count=3`.
- Proceed to `/ases-critique T-073 V2`.
