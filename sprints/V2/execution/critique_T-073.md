# Critique — T-073 (iteration 4)

**Files:** `backend/src/presentation/api/routers/users.py`, `backend/src/application/services/auth_service.py`
**Sprint:** V2 · **Module:** M-008 · **Critic:** Opus 4.7
**Verdict:** `CLEAN`
**Issues remaining:** 0 (previous: 6) · **Iteration:** 4 · **Prior escalation:** resolved by PO Option A (2026-07-05)

## Summary

All 6 findings from iteration 3 are resolved by the PO-authorized bounded scope amendment (Option A, 2026-07-05):

- `T-073 output_files[]` amended to include `auth_service.py` for two new methods only.
- `sprints/V2/design/lld.json` amended: `files[users.py]` declares 5 endpoints, `files[auth_service.py]` declares 7 methods (added `get_user`, `deactivate_user`).
- `AuthService.get_user(user_id)` — read-only fetch via `self._repo.get(user_id)`, no commit. Restores HTTP GET safety per RFC 9110 §9.2.1.
- `AuthService.deactivate_user(user_id)` — canonical soft-delete via `self._repo.soft_delete(user_id); self._db.commit()` per DS-008.
- Router `get_user` handler → `return svc.get_user(user_id)`.
- Router `deactivate_user` handler → `svc.deactivate_user(user_id); return None` — FastAPI honors `status_code=204` on the decorator.
- Inline workaround comment removed; `Response` dropped from `fastapi` import list.

Four lenses pass; structural lens confirms the router is mounted at `main.py:70` and both new methods are reachable through the FastAPI entry point.

## Resolved findings (from iter3)

| ID | Lens | Was | Now |
|---|---|---|---|
| F-073-01 | spec (major) | GET /{user_id} bound to `svc.update_user(user_id, UserUpdate())` — no `svc.get_user` existed. | `users.py:34` → `return svc.get_user(user_id)`. `auth_service.py:77-78` → `AuthService.get_user`. |
| F-073-02 | test (major) | GET committed on every read (`update_user` calls `self._db.commit()`) — RFC 9110 safe-method violation. | GET path is read-only end-to-end. `AuthService.get_user` performs no writes and no commit. |
| F-073-03 | spec (major) | DELETE /{user_id} bypassed `BaseRepository.soft_delete` (DS-008 canonical primitive) via `update_user(id, UserUpdate(is_active=False))`. | `users.py:53` → `svc.deactivate_user(user_id)`. `auth_service.py:92-95` → `self._repo.soft_delete(user_id); self._db.commit()`. |
| F-073-04 | contract (minor) | Inline workaround comment documenting intentional API misuse. | Removed. |
| F-073-05 | spec (info) | `Response` imported and explicit `Response(status_code=204)` returned on DELETE. | `Response` removed from imports; DELETE handler returns `None`. |
| F-073-06 | spec (info) | LLD declared 3 endpoints + 5 AuthService methods; plan expanded to 5 endpoints + 2 new methods. | LLD amended — `files[users.py]` = 5 endpoints; `files[auth_service.py]` = 7 methods. Plan `scope_amendment_note` captures the authorization. |

## Lens results

- **Spec** — PASS. 5 endpoints in `users.py`; both new `AuthService` methods match LLD signatures (lines 167-181) exactly.
- **Contract** — PASS. `router` imported at `main.py:23`, mounted at `main.py:70`. All dependency, service, schema, and model imports resolve.
- **Test** — PASS. TC-211 (STAFF → 403) and TC-212 (SUPERVISOR → 201) still satisfied. New paths (GET/DELETE `{user_id}`) are behaviorally correct — HTTP-safe read and DS-008 soft-delete respectively.
- **Security** — PASS. All 5 endpoints chain `require_supervisor` → `get_current_user` (JWT + `is_active` DB re-check per DS-018). New service methods carry no new attack surface.
- **Structural** — PASS. `graphify-out/graph.json` present. `NotFoundError` from `BaseRepository.get` / `.soft_delete` translates to HTTP 404 via `presentation/api/errors.py:9`. No orphaned functions, no dead imports.

## Decisions touched
`DS-007` (four-layer boundary preserved) · `DS-008` (soft-delete canonical primitive now used on DELETE) · `DS-018` (JWT + is_active re-check chain intact) · `DS-019` (SUPERVISOR role check at all 5 endpoints).

## Iteration history

| Iter | Verdict | Issues flagged | Issues resolved |
|---|---|---|---|
| 1 | FIX_REQUIRED | 5 | 0 |
| 2 | FIX_REQUIRED | 6 | 0 |
| 3 | ESCALATE | 6 | 0 |
| 4 | **CLEAN** | 0 | **6** |

## Next action

- `tasks.json` T-073: `status → complete`, `iteration_count = 4`, `critique_verdict = CLEAN`.
- `.ases/context.json`: append `critique:T-073:V2:iter4:CLEAN` to `completed_steps`; clear T-073 blocker.
- V2 has no remaining `in_progress` tasks → `/ases-sprint-close V2` unblocked.
- Non-blocking follow-up already logged: DS-024 (auth form-encoded wire format) to be added at `/ases-sprint-close V2` (from T-072 iter3 CLEAN note).

## Artifacts

- Critique JSON: `sprints/V2/execution/critique_T-073.json`
- Critique MD: `sprints/V2/execution/critique_T-073.md`
- Iter3 escalation snapshot: `sprints/V2/execution/snapshots/T-073-escalation-3.json`
- Iter4 fix snapshot: `sprints/V2/execution/snapshots/T-073-fix-4.json`
