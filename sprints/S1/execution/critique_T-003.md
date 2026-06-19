# T-003 — Critique

**Produced by:** `/ases-critique T-003 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-003.json](./critique_T-003.json)
**Reviewed file:** [backend/src/domain/exceptions.py](../../../backend/src/domain/exceptions.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** |
| Contract | **PASS** |
| Test | **PASS** — TC-017/027/028 supported via `self.message` + `self.entity` + `self.id_` |
| Security | **PASS** |
| Structural | DEFERRED |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

---

## Lens-by-lens

### 1 · Spec — PASS

4 classes, in this order, matching LLD `files[6]` verbatim:

| Class | Constructor | Stored attrs |
|-------|------------|--------------|
| `DomainError(Exception)` | `(message: str)` | `message` |
| `NotFoundError(DomainError)` | `(entity: str, id_: int)` | `message`, `entity`, `id_` (auto-formatted message) |
| `ConflictError(DomainError)` | inherited `(message: str)` | `message` |
| `ValidationError(DomainError)` | inherited `(message: str)` | `message` |

No extra helpers, no scope creep.

### 2 · Contract — PASS

Downstream consumers verified:

| Task | Usage | OK? |
|------|-------|-----|
| T-005 `BaseRepository` | `raise NotFoundError(entity, id_)` | ✓ |
| T-008 `register_error_handlers` | maps 4 classes → 404/409/422/500; reads `message` | ✓ |
| T-013 `GradeService.create_grade` | `raise ConflictError(f"grade_code '{...}'")` | ✓ |
| T-015 `DesignGradeMapService.create_mapping` | `NotFoundError('TradingDesign', id)`, `NotFoundError('Grade', id)`, `ConflictError(...)` | ✓ |
| T-010..T-014 services | NotFoundError pattern | ✓ |

No imports → DS-007 layering invariant preserved (domain layer cannot reach into other project modules).

### 3 · Test — PASS

Indirect test refs (resolved at service layer): TC-017, TC-027, TC-028, TC-035, TC-038.

| TC | Assertion | Supported by |
|----|-----------|--------------|
| TC-017 | `error_message_contains: "grade_code"` | `self.message` exposes the f-string GradeService builds |
| TC-027 | `error_entity: "TradingDesign"` | `self.entity` attribute |
| TC-028 | `error_entity: "Grade"` | `self.entity` attribute |
| TC-035 | 409 body detail contains "grade_code" | T-008 mapper reads `self.message` |
| TC-038 | 409 body detail contains "design_id, grade_id" | T-008 mapper reads `self.message` |

Manual smoke during `/ases-dev`:
- `NotFoundError('Foo', 1)` → `Foo with id 1 not found` with `entity='Foo'`, `id_=1` ✓
- `ConflictError` / `ValidationError` accept arbitrary message ✓
- All 3 subclasses inherit from `DomainError` ✓

### 4 · Security — PASS

- f-string parameters are typed (`entity: str`, `id_: int`) — no injection surface even with hostile input.
- No SQL, shell, or filesystem access.
- No secrets, no credentials.
- Clean single-inheritance chain.

### 5 · Structural — DEFERRED

4 leaf classes with zero current importers. Graphify rebuild after T-015 lands will surface the inbound edges from T-005 / T-008 / T-010..T-015.

---

## Disposition

Mark T-003 `status=complete` in [tasks.json](./tasks.json). Next task: **`/ases-validate T-007 S1`** (Pydantic schemas — also parallel-group 1, zero deps) or **`/ases-validate T-004 S1`** (ORM models — T-002 is complete, this unlocks the ORM track).
