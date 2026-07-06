# Critique — T-069 | Sprint V2 | Iteration 2

**Task:** schemas/auth.py — Pydantic v2 auth schemas  
**File:** `backend/src/presentation/schemas/auth.py`  
**Verdict:** `CLEAN`  
**Issues remaining:** 0 (was 1 in iteration 1)  
**Timestamp:** 2026-07-02

---

## Iteration 1 Fix Verified ✅

SEC-001 (UserUpdate.new_password missing `min_length=8`) was flagged in iteration 1. The fix has been applied:

```python
# iteration 1 (wrong)
new_password: str | None = None

# iteration 2 (correct)
new_password: str | None = Field(default=None, min_length=8)
```

Password strength policy is now consistent across `UserCreate.password` and `UserUpdate.new_password`. Issue closed.

---

## Lens 1 — Spec ✅ PASS

All five schemas match the plan.json scope and LLD description:

| Schema | Fields | Constraints | Config |
|---|---|---|---|
| `LoginRequest` | username (str), password (str) | password min_length=1 | — |
| `TokenResponse` | access_token (str), token_type (Literal['bearer']), role (str) | — | — |
| `UserCreate` | username (str), password (str), role (Literal) | username 1–100 chars, password min 8 | — |
| `UserRead` | id (int), username (str), role (str), is_active (bool) | — | from_attributes=True ✓ |
| `UserUpdate` | is_active, role, new_password | all Optional; new_password min_length=8 ✓ | — |

**definition_of_done checklist:**
- [x] File exports exactly 5 schemas
- [x] No project imports
- [x] UserRead has from_attributes=True
- [x] UserUpdate all fields Optional

---

## Lens 2 — Contract ✅ PASS

- LLD `interfaces.exports = ['LoginRequest','TokenResponse','UserCreate','UserRead','UserUpdate']` — all present.
- LLD `interfaces.expects = ['pydantic.BaseModel','pydantic.ConfigDict']` — both imported; `Field` additionally imported and used.
- No project-level imports.
- Downstream consumers resolve correctly:
  - `auth_service.py`: `TokenResponse`, `UserCreate`, `UserUpdate` ✓
  - `routers/auth.py`: `LoginRequest`, `TokenResponse`, `UserRead` ✓
  - `routers/users.py`: `UserCreate`, `UserRead`, `UserUpdate` ✓

---

## Lens 3 — Test ✅ PASS

`test_case_refs: []` — no test cases directly target T-069 (`test_required: false` in LLD).

Downstream test coverage verified:
- **TC-190..TC-194** (AuthService tests): consume `TokenResponse` + `UserRead` — shapes match ✓
- **TC-208..TC-210** (router tests): assert `TokenResponse`/`UserRead` body shapes ✓
- **TC-212** (POST /users): `UserCreate` body + `UserRead` response match ✓

Manual success criteria:
- `UserRead.model_config['from_attributes'] is True` ✓
- `UserRead.model_fields.keys() → {'id','username','role','is_active'}` ✓

---

## Lens 4 — Security ✅ PASS

All security checks pass:

- `LoginRequest.password min_length=1` — prevents empty-string bcrypt calls ✓
- `UserCreate.password min_length=8` — enforces strong passwords at creation ✓
- `UserUpdate.new_password min_length=8` — prevents password downgrade below policy floor ✓ *(SEC-001 fix)*
- `UserCreate.role: Literal[...]` — enum validation at schema level ✓
- `UserUpdate.role: str | None` — no Literal constraint; **ADR tradeoff DS-019**: role validation delegated to ORM Enum column + DB CHECK constraint (not a defect)
- No hardcoded secrets, no injection vectors, no sensitive field exposure

---

## Lens 5 — Structural ⬜ SKIP

Pure Pydantic `BaseModel` class definitions with no callable logic and no project imports. Call-graph analysis not applicable.

---

## Verdict: CLEAN

All lenses pass. SEC-001 resolved. T-069 status → **complete**.

**Next:** T-069 unblocks T-071 (AuthService). Proceed to `/ases-validate T-071 V2`.
