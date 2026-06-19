# T-013 — Critique

**Verdict:** **CLEAN** · Iteration 1/3 · 2026-06-18
**Reviewed:** [backend/src/application/services/grade_service.py](../../../backend/src/application/services/grade_service.py)
**Companion JSON:** [critique_T-013.json](./critique_T-013.json)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 4 methods + AC-011 ConflictError pre-check + grade_code.strip() (N-001 fix) |
| Contract | **PASS** — T-016 + T-020 satisfied |
| Test | **PASS** — TC-017, TC-035, rename-to-same, N-001 all verified inline |
| Security | **PASS** |
| Structural | PASS |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

**Resolved warning: N-001 ✅** (whitespace bypass at AC-011 layer).

---

## Lens-by-lens

### 1 · Spec — PASS

Implementation matches plan.md verbatim, plus an in-scope addition:

| Method | Behaviour |
|--------|-----------|
| `list_grades(include_inactive=False)` | `repo.list` → `[GradeRead.model_validate(r) for r in ...]` |
| `create_grade(payload)` | **strip** grade_code → pre-check `repo.get_by_code(code)` → `ConflictError("grade_code '{code}' already exists")` on duplicate → `repo.create({'grade_code': code})` + commit + Read |
| `update_grade(id, patch)` | dump with `exclude_none=True`; if `grade_code` in patch: strip + uniqueness check excluding own row (`existing.grade_id != grade_id`); then `repo.update` + commit + Read |
| `deactivate_grade(id)` | `repo.soft_delete` (DS-008) + commit + Read |

The `.strip()` addition is **not** in plan.md text but is in scope per:
- LLD `files[13]`: `grade_code constr min_length=1, strip_whitespace`
- schema.json: `CHECK grade_code <> '' (enforced via Pydantic constr min_length=1, strip_whitespace)`
- T-007 plan.md: `# strip in service if needed`
- context.json `open_issues`: N-001 explicitly flagged for T-013 to address

Stays inside `output_files[] = ["backend/src/application/services/grade_service.py"]`.

### 2 · Contract — PASS

| Downstream | Uses | OK? |
|-----------|------|-----|
| T-016 `get_grade_service` | `GradeService(db)` ctor | ✓ |
| T-020 grades router | `service.{list,create,update,deactivate}_grade` | ✓ |

### 3 · Test — PASS

Inline `/ases-dev` smokes (all via MagicMock so no DB needed):

| Scenario | Result |
|----------|--------|
| **TC-017** — duplicate grade_code `'1'` → ConflictError | ✓ message: `grade_code '1' already exists` |
| **TC-035** — 409 body detail contains `'grade_code'` | ✓ substring present |
| **N-001** — `'  DIM  '` strip | ✓ `get_by_code` called with `'DIM'`; `repo.create` called with `{'grade_code': 'DIM'}` |
| **Rename-to-same** — `update_grade(5, {'grade_code': 'DIM'})` when row 5 already has `'DIM'` | ✓ no false ConflictError; guard `existing.grade_id != grade_id` works |

TC-019 (AC-012 effect on design-grade list) is exercised at T-015 `list_active_grades_for_design` (downstream JOIN filter); T-013's deactivate just sets `is_active=False`.

### 4 · Security — PASS

- Pydantic enforces `min_length=1` upstream on `grade_code` (T-007).
- All DB access via parameterised SQLAlchemy.
- `.strip()` is deterministic and safe (no regex, no eval).
- ConflictError detail is f-string with Pydantic-validated input; JSON-escaped by FastAPI on the wire.
- No raw SQL/shell/FS/secrets.

### 5 · Structural — PASS

Single class, 4 methods. Imports: `Session`, `GradeRepository`, 3 schemas, `ConflictError` — all used. Inbound: T-006 ✓, T-007 ✓, T-003 ✓.

---

## Resolved warnings

### ✅ N-001 — `grade_code` whitespace strip

Flagged in T-007 critique (carried in context.json). Resolved at the service boundary in T-013: `.strip()` applied before BOTH the pre-check lookup AND the repo write, in both `create_grade` and `update_grade`. AC-011 UNIQUE protection now honours the LLD's `strip_whitespace` intent.

---

## Soft notes (informational)

### N-001-disposition · Service-level vs Pydantic-level strip

LLD originally specified `strip_whitespace` at the Pydantic constr() level (request boundary). The chosen implementation strips at the service boundary instead. Functionally equivalent because the service is the only legitimate consumer of `GradeCreate` (DS-012 forbids bypassing it). At sprint-close, optionally migrate to `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]` for defence-in-depth. Out of scope for S1.

---

## Disposition

Mark T-013 `status=complete` in [tasks.json](./tasks.json). Flip N-001 to RESOLVED in [.ases/context.json](../../../.ases/context.json). Proceed to **`/ases-validate T-014 S1`** (DesignService — canonical pattern).
