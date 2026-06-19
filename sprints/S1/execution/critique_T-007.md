# T-007 — Critique

**Produced by:** `/ases-critique T-007 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-007.json](./critique_T-007.json)
**Reviewed file:** [backend/src/presentation/schemas/master.py](../../../backend/src/presentation/schemas/master.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 19 schemas, Pydantic v2 idioms, `from_attributes=True` on Read |
| Contract | **PASS** — T-010..T-015 services + T-017..T-022 routers satisfied |
| Test | **PASS** — TC-002/003/009/013/021 all verified inline |
| Security | **PASS** — Pydantic validation at the boundary, no leak in Read shape |
| Structural | PASS — single file, clean imports |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

**Headline resolution:** UR-W002 ✅ — all 6 `*Update` schemas declare `is_active: bool | None = None`, unblocking the frontend Reactivate flow end-to-end.

---

## Lens-by-lens

### 1 · Spec — PASS

19 schemas in LLD order:

| Entity | Create | Update | Read | Special |
|--------|--------|--------|------|---------|
| Supplier | ✓ | ✓ + `is_active?` | ✓ from_attributes | — |
| Staff | ✓ | ✓ + `is_active?` | ✓ from_attributes | no `created_at` not applicable (has it) |
| Dealer | ✓ | ✓ + `is_active?` | ✓ from_attributes | — |
| Grade | ✓ | ✓ + `is_active?` | ✓ from_attributes | **no `created_at`** |
| Design | ✓ | ✓ + `is_active?` | ✓ from_attributes | — |
| DesignGradeMap | ✓ `Field(gt=0)` on FKs | ✓ (`is_active?` only) | ✓ + Optional `design_name`/`grade_code` | **no `created_at`** |
| (minimal) | — | — | `DesignGradeReadMin {grade_id, grade_code}` | DF-006 / AC-019 contract |

### 2 · Contract — PASS

Downstream callers:

| Task | Uses | OK? |
|------|------|-----|
| T-010..T-014 services | `XCreate.model_dump()`, `XUpdate.model_dump(exclude_none=True)`, `XRead.model_validate(orm)` | ✓ |
| T-015 service | DesignGradeMap CRUD + `DesignGradeReadMin` for AC-019 | ✓ |
| T-017..T-022 routers | `response_model=XRead`, request body `XCreate`/`XUpdate` | ✓ |
| T-008 errors handler | propagates `pydantic.ValidationError` to 422 via FastAPI default | ✓ |

Imports: `datetime`, `pydantic.{BaseModel, ConfigDict, Field}` — all used. No project module imports (DS-007 preserved).

### 3 · Test — PASS

All 5 declared TCs verified inline during `/ases-dev`:

| TC | Input | Expected error_type | Result |
|----|-------|---------------------|--------|
| TC-002 | `SupplierCreate(supplier_name='', place='Mallur')` | `string_too_short` on `supplier_name` | ✓ |
| TC-003 | `SupplierCreate(supplier_name='Foo', place='')` | `string_too_short` on `place` | ✓ |
| TC-009 | `StaffCreate(staff_name='')` | `string_too_short` on `staff_name` | ✓ |
| TC-013a | `DealerCreate(dealer_name='', place='X')` | `string_too_short` on `dealer_name` | ✓ |
| TC-013b | `DealerCreate(dealer_name='Raj', place='')` | `string_too_short` on `place` | ✓ |
| TC-021a | `DesignCreate(size='', design_name='X')` | `string_too_short` on `size` | ✓ |
| TC-021b | `DesignCreate(size='16X10', design_name='')` | `string_too_short` on `design_name` | ✓ |

Bonus checks: `DesignGradeMapCreate(design_id=0, grade_id=1)` rejected by `gt=0`; `SupplierRead.model_validate(FakeORMSupplier())` produces a valid Read DTO; UR-W002 verified via `SupplierUpdate(is_active=True)` etc on all 6 entities.

### 4 · Security — PASS

- All input validation at Pydantic boundary — no manual parsing.
- `min_length=1` rejects empty strings before they reach service/repo.
- `gt=0` on FK integers prevents negative IDs.
- `from_attributes=True` is on Read schemas **only** (response shape) — never on Create/Update, so no ORM-attribute injection via request bodies.
- No exposed secrets — these are pure validation classes.

### 5 · Structural — PASS

Single file, 20 classes (1 base + 18 concrete + 1 minimal projection). No project imports → DS-007 layering preserved. Outbound edges form as services + routers + frontend types consume these.

---

## Soft notes (non-blocking)

### N-001 · `grade_code` whitespace stripping deferred to service

LLD `files[13]` and `schema.json` both specify `grade_code constr min_length=1, strip_whitespace`. The plan.md explicitly deferred this with the comment `# strip in service if needed` — implementation follows plan.md.

**Risk:** without stripping, a user could submit `'  DIM  '` and bypass UNIQUE collision with seeded `'DIM'` → AC-011 bypass.

**Mitigation (actionable for T-013):** GradeService.create_grade should `payload.grade_code.strip()` before `get_by_code()` and `repo.create(...)`. If T-013 plan.md doesn't already include this, T-013 critic should flag.

### N-002 · DealerUpdate.is_active is intentional addition vs brief LLD prose

LLD's brief `"All fields Optional; partial update"` description for `*Update` schemas doesn't enumerate `is_active`. The explicit field on all 6 schemas is required by **UR-W002** (ui_review) and is correct — logging only so future critique passes don't mistake this for drift.

---

## Disposition

Mark T-007 `status=complete` in [tasks.json](./tasks.json). Mark UR-W002 as RESOLVED in [.ases/context.json](../../../.ases/context.json) `open_issues`. Proceed to **`/ases-validate T-008 S1`** (FastAPI error handlers — depends on T-003 only, complete).
