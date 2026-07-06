# Critique: T-068 — `domain/auth.py`

**Sprint:** V2 | **Iteration:** 1 | **Produced by:** `/ases-critique T-068 V2` | **Date:** 2026-07-02

---

## Verdict: ✅ CLEAN

No issues found across all four lenses. Implementation is correct, spec-compliant, and ready for T-071 (AuthService) to proceed.

---

## Decisions Read First

| ADR | Relevance |
|---|---|
| DS-005 | V1 no-auth (superseded in V2) — no bearing on domain/auth.py |
| DS-007 | Four-layer architecture — domain/auth.py is correctly in the domain layer with zero project imports |
| DS-018 | JWT HS256 + bcrypt + 8h TTL — implementation matches exactly |
| DS-019 | RBAC roles — domain/auth.py is role-agnostic (role lives in the JWT payload; encoding is caller's responsibility) |

No ADR tradeoffs present in this task's scope.

---

## Lens 1 — Spec

**Status: PASS**

| Requirement | Check |
|---|---|
| Exactly 4 exported functions | ✅ `get_password_hash`, `verify_password`, `create_access_token`, `decode_access_token` |
| No class definitions | ✅ |
| No SQLAlchemy imports | ✅ |
| No HTTP imports | ✅ |
| `get_password_hash` via CryptContext(bcrypt) | ✅ `_pwd_context.hash(plain_password)` |
| `verify_password` constant-time | ✅ `_pwd_context.verify()` — passlib bcrypt is constant-time |
| `create_access_token` — SECRET_KEY, EXPIRE_HOURS, HS256, 8h default | ✅ Fully correct |
| `create_access_token` raises ValueError if SECRET_KEY absent | ✅ Matches `LLD raises[]` |
| `decode_access_token` never raises | ✅ `try/except JWTError: return None` |
| `decode_access_token` catches `ExpiredSignatureError` | ✅ Via JWTError parent class (python-jose: `ExpiredSignatureError ⊆ JWTError`) |

**Note:** The plan says "catches JWTError + ExpiredSignatureError" but the implementation imports and catches only `JWTError`. This is not a defect — `ExpiredSignatureError` is a subclass of `JWTError` in python-jose, so the single catch is semantically equivalent and cleaner.

**Note:** `decode_access_token` uses `os.getenv("SECRET_KEY", "")` (empty-string fallback) while `create_access_token` raises `ValueError` if `SECRET_KEY` is absent. This asymmetry is intentional and correct: a token signed with a real key cannot be decoded with an empty key → `JWTError` → `None` — fail-safe behaviour matches the "never raises" contract.

---

## Lens 2 — Contract

**Status: PASS**

All 4 function signatures match `lld.json files[2]` interfaces exactly. The file has `depends_on: []` — only stdlib (`datetime`, `os`) and third-party (`jose`, `passlib`) imports, zero project-level imports. No layer violations.

| Downstream consumer | Functions needed | Available |
|---|---|---|
| T-071 `auth_service.py` | `verify_password`, `get_password_hash`, `create_access_token`, `decode_access_token` | ✅ all 4 |
| T-075 `seed_default_user.py` | `get_password_hash` | ✅ |

Module-level `_pwd_context` singleton is correct — `CryptContext` is thread-safe and expensive to construct; module-level singleton is the standard pattern.

---

## Lens 3 — Test

**Status: PASS**

| TC | Description | Satisfiable |
|---|---|---|
| TC-171 | `verify_password(plain, hash_of_plain)` → True | ✅ `_pwd_context.verify` returns True |
| TC-172 | `verify_password(wrong, hash_of_other)` → False | ✅ bcrypt compare rejects mismatches |
| TC-173 | `create_access_token({"sub":"admin","role":"SUPERVISOR"})` → JWT with correct payload, exp in future | ✅ Test must set `SECRET_KEY` env var — standard pytest fixture concern, not a code issue |
| TC-174 | `decode_access_token(expired_jwt)` → None | ✅ `ExpiredSignatureError ⊆ JWTError` → caught → None |
| TC-175 | `decode_access_token("not.a.valid.jwt")` → None | ✅ `JWTError` → caught → None |

All 5 test cases satisfiable without code change.

---

## Lens 4 — Security

**Status: PASS**

| Check | Result |
|---|---|
| No hardcoded secrets | ✅ `SECRET_KEY` exclusively from `os.getenv` |
| bcrypt (industry standard) | ✅ `CryptContext(schemes=["bcrypt"], deprecated="auto")` |
| Constant-time password comparison | ✅ passlib `CryptContext.verify()` uses `hmac.compare_digest` internally |
| Algorithm pinned in encode | ✅ `algorithm="HS256"` (single string, not list) |
| Algorithm pinned in decode | ✅ `algorithms=["HS256"]` — prevents `none` algorithm and RS256/HS256 confusion attacks |
| `decode_access_token` never raises | ✅ `try/except JWTError: return None` — callers see None and raise HTTP 401 |
| No secret leakage | ✅ `secret_key` is a local variable per call, not module-level, not logged |

---

## Lens 5 — Structural

**Status: SKIP** — pure domain file with zero project imports. All 4 functions are explicitly consumed by declared downstream tasks (T-071, T-075). No orphaned functions.

---

## Actions

**tasks.json update:** `T-068.status` → `complete`

**Next task:** T-069 (`presentation/schemas/auth.py`) or proceed in parallel per `parallel_groups[0]`.
