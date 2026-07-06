# Critique: T-071 — AuthService
**Sprint:** V2 · **Iteration:** 1 · **Verdict:** ✅ CLEAN

## Summary
`AuthService` passes all four lenses. Five methods are implemented correctly and match `plan.json`, `lld.json` signatures, and the five test-case references (TC-190..TC-194). Commit lifecycle, error codes, and password handling are consistent with the established S1 pattern.

---

## Lens 1 — Spec ✅

| Method | Plan spec | Implementation | Status |
|--------|-----------|----------------|--------|
| `authenticate` | lookup → is_active check (401) → verify_password (401) → TokenResponse | Combined `not user or not user.is_active` → 401; wrong password → 401; TokenResponse with role | ✓ |
| `get_current_user` | decode_access_token → None→401; DB fetch by sub → inactive→401 | Exact flow; sub=None guard added | ✓ |
| `create_user` | uniqueness check → 409; hash; persist; return UserModel | get_by_username → HTTPException 409; `get_password_hash`; repo.create; commit; return obj | ✓ |
| `list_users` | repo.list_active() | `self._repo.list_active()` | ✓ |
| `update_user` | fetch → 404; apply patches; return UserModel | Patch dict built from non-None fields; `repo.update` (NotFoundError → global 404 handler); commit | ✓ |

**Commit pattern** verified consistent with S1: `SupplierService.create_supplier` also calls `session.commit()` at service layer after `repo.create`. ✓

**Return type**: `UserModel` (ORM object) returned from all write methods, unlike S1 services which return Pydantic models. This is intentional per LLD — the auth router (T-072) will apply `UserRead.model_validate(user)`. ✓

### Minor LLD discrepancy (I-002)
`lld.json` `authenticate.raises[1]` says `HTTPException 403 account deactivated`. Both `plan.json` ("`401 if not found or inactive`") and TC-192 specify 401. Implementation is correct. LLD documentation error — no code change needed.

---

## Lens 2 — Contract ✅

| Import | Source | Status |
|--------|--------|--------|
| `create_access_token, decode_access_token, get_password_hash, verify_password` | `src.domain.auth` | ✓ |
| `UserModel` | `src.infrastructure.db.models.auth` | ✓ |
| `UserRepository` | `src.infrastructure.db.repositories.auth` | ✓ |
| `TokenResponse, UserCreate, UserUpdate` | `src.presentation.schemas.auth` | ✓ |

Exports `AuthService` as specified in `lld.json interfaces.exports`. Downstream tasks T-072 (auth router) and T-073 (users router) can call all 5 methods as expected. ✓

---

## Lens 3 — Test ✅

| TC | Scenario | Expected | Implementation outcome |
|----|----------|----------|----------------------|
| TC-190 | Valid creds | TokenResponse(bearer, SUPERVISOR) | `verify_password` passes; `create_access_token`; TokenResponse built with `role=user.role` (string enum "SUPERVISOR") | ✓ |
| TC-191 | Wrong password | HTTPException 401 | is_active=True passes first guard; `verify_password` → False → raise 401 | ✓ |
| TC-192 | is_active=False | HTTPException 401 | `if not user or not user.is_active:` → True → raise 401 before password check | ✓ |
| TC-193 | Valid JWT | UserModel returned | `decode_access_token` → payload; sub="admin"; `get_by_username`; is_active=True; return user | ✓ |
| TC-194 | Duplicate username | HTTPException 409 | `get_by_username("dupuser")` is not None → raise 409 | ✓ |

---

## Lens 4 — Security ✅

| Check | Result |
|-------|--------|
| Password hashed before persist | `get_password_hash(data.password)` called before `repo.create()` ✓ |
| No JWT payload in error messages | "Invalid credentials" / "Could not validate credentials" — no token data leaked ✓ |
| Input validation | `UserCreate.password: str = Field(min_length=8)` in schema ✓ |
| No raw SQL | All operations via UserRepository / BaseRepository ORM ✓ |

### I-001 — Timing side-channel (minor, ADR tradeoff)
`if not user or not user.is_active:` returns without bcrypt (~0ms). Wrong-password path invokes bcrypt (~100ms). Timing difference could allow username/activity enumeration.

**Why this is acceptable**: DS-018 makes no mention of constant-time comparison; V2 is an internal single-tenant system; all 401 responses carry the same error message (no semantic leakage). No code change required.

---

## Issues

| ID | Lens | Severity | Description | Action |
|----|------|----------|-------------|--------|
| I-001 | security | minor | Timing side-channel in authenticate (bcrypt skip on non-existent/inactive user) | ADR tradeoff — no change, document |
| I-002 | spec | minor | LLD authenticate.raises[1] says 403; plan + TC-192 say 401. Implementation correct; LLD has doc error | Fix lld.json at next schema maintenance pass |

---

## Out-of-Scope Notes

- `UserUpdate.role: str | None` in `schemas/auth.py` lacks a Pydantic `Literal["STAFF","VERIFIER","SUPERVISOR"]` constraint. Invalid role strings would fail at the DB Enum level (IntegrityError → 409 via global handler), giving a less informative error than a 422. This is a T-069 schema issue, not in T-071's `output_files[]`.

---

## Verdict: CLEAN ✅
**0 critical · 0 major · 2 minor (both acceptable)**

Next: update `tasks.json` T-071 → status=complete, iteration_count=1 → proceed to `/ases-validate T-072 V2`.
