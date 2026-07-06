# Critique — T-092 (iteration 3)

**Task:** MODIFY `backend/src/main.py` — mount 6 V2 routers + add auth dep to all V1 router mounts
**Sprint:** V2 · **Module:** M-008 · **Iteration:** 3 · **Previous verdict:** FIX_REQUIRED
**Verdict:** ✅ **CLEAN**

## Summary

Iteration 3 re-audit after `/ases-fix`. Every critical + major finding from iteration 2 is resolved:

- **F-092-1, F-092-2 (critical, spec + test):** all six V2 `include_router` calls now carry `prefix="/api/v1"`; endpoints resolve at the DS-010 / TC-208..TC-217 paths and `oauth2_scheme.tokenUrl='/api/v1/auth/login'` matches the live mount.
- **F-092-3 (major, contract):** `inward_report.py` imports fixed out-of-scope to use `src.`-prefixed paths, consistent with the other 5 V2 routers and `main.py`'s own import style — `python -m uvicorn src.main:app` now imports cleanly.
- **F-092-4 (minor, spec drift, `is_adr_tradeoff`):** accepted as-built. Documented inline via comments on `main.py:64` and `main.py:68-69`. Non-blocking recommendation: capture as `DS-024` at sprint-close.

Counts: **0 critical · 0 major · 0 minor · 1 residual accepted tradeoff.**

## Resolution Ledger

| ID | Prior | Status | Evidence |
|---|---|---|---|
| F-092-1 | critical | ✅ RESOLVED | `main.py:59,65,66,70,71,72` — every V2 `include_router` now has `prefix="/api/v1"`. |
| F-092-2 | critical | ✅ RESOLVED | `main.py:59` — `auth_router` mounted at `/api/v1`; `POST /api/v1/auth/login` matches `dependencies.py oauth2_scheme.tokenUrl`. |
| F-092-3 | major    | ✅ RESOLVED | `backend/src/presentation/api/routers/inward_report.py:19-22` — all imports now `src.`-prefixed. |
| F-092-4 | minor    | ⚠️ ACCEPTED | Mount-level dep intentionally omitted on 5 non-auth V2 routers; route-level `Depends` per file; FastAPI dedups; behaviorally equivalent; TC-213 unaffected. Comments document intent. |

## Regression Checks

- ✅ **V1 routers still guarded** — 11 calls on `main.py:45-55` retain `dependencies=[Depends(get_current_user)]`. TC-213 satisfied.
- ✅ **Mount order preserved** — `report_export_router` (line 65) mounted before `inward_report_router` (line 66); `/api/v1/reports/inward/export` cannot be swallowed by the inward router.
- ✅ **auth router open** — no mount-level dep on `auth_router` (`DS-018`); `/api/v1/auth/login` reachable without a token.
- ✅ **CORS / lifespan / /health untouched** — `do_not_touch` clause honored.
- ✅ **Scope compliance** — only `backend/src/main.py` touched by T-092; F-092-3 fix routed to owning task (inward_report.py).

## Next Action

- Set T-092 → `status=complete`, `critique_verdict=CLEAN`, `iteration_count=3` in `sprints/V2/execution/tasks.json`.
- Update `.ases/context.json` → `last_completed_task=T-092`.
- **T-092 is the final task in `execution_order[]`.** Proceed to `/ases-sprint-close V2`.
- (Optional, non-blocking) At sprint-close, add `DS-024` capturing the deliberate LLD-prose drift on V2 non-auth mount deps.
