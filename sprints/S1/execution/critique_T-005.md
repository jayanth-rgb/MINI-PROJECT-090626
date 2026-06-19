# T-005 — Critique

**Produced by:** `/ases-critique T-005 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-005.json](./critique_T-005.json)
**Reviewed file:** [backend/src/infrastructure/db/repositories/base.py](../../../backend/src/infrastructure/db/repositories/base.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 5 methods + ctor + `__class_getitem__` match LLD `files[4]` |
| Contract | **PASS** — T-006 subclassing pattern works; T-010..T-015 service signatures all matched |
| Test | **PASS** — 17 indirect TC refs supported (include_inactive filter, NotFoundError, soft-delete preserves row) |
| Security | **PASS** — parameterised SQL, validated input via Pydantic upstream |
| Structural | PASS — clean imports, no orphans |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

---

## Decisions consulted (M-007)

DS-007 (layering), DS-008 (soft delete — no `delete()` method), DS-012 (generic CRUD pattern). All satisfied at structural level.

---

## Lens-by-lens

### 1 · Spec — PASS

| Method | Verified |
|--------|----------|
| `__init__(session: Session)` | ✓ |
| `list(include_inactive=False)` | ✓ filter via `self.model.is_active.is_(True)` when default |
| `get(id_)` | ✓ raises `NotFoundError(entity, id_)`; entity from `self.model.__name__.removesuffix('Model')` |
| `create(data: dict)` | ✓ `self.model(**data)` + add + flush |
| `update(id_, patch: dict)` | ✓ get → setattr (skip None) → flush |
| `soft_delete(id_)` | ✓ get → `is_active = False` → flush |
| **NO `delete()` method** | ✓ DS-008 invariant — verified via `hasattr(..., 'delete') == False` |

`Generic[TModel]` + `__class_getitem__` correctly binds `self.model` on subclass — verified during `/ases-dev` with `BaseRepository[SupplierModel].model is SupplierModel`.

### 2 · Contract — PASS

| Downstream | Pattern | OK? |
|-----------|---------|-----|
| T-006 `SupplierRepository(BaseRepository[SupplierModel])` | sub-of-sub subclass via `__class_getitem__` | ✓ |
| T-006 `GradeRepository.get_by_code` | extends base without override | ✓ |
| T-006 `DesignGradeMapRepository.{list_active_by_design,get_by_pair}` | extends base | ✓ |
| T-010..T-015 service calls `repo.list(include_inactive=...)`, `.create(model_dump())`, `.update(id, model_dump(exclude_none=True))`, `.soft_delete(id)` | every signature matches | ✓ |
| T-009 conftest passes Session to repo ctor | supported | ✓ |

All imports used: `Any, Generic, Type, TypeVar` from typing; `select` from sqlalchemy; `Session` from sqlalchemy.orm; `NotFoundError` (T-003); `Base` (T-002).

### 3 · Test — PASS

17 indirect TC refs (TC-001/004/005/006/008/010/012/014/017/019/020/023/024/025/029/031/032). Key behaviours:

| Behaviour | Test | Supported? |
|-----------|------|-----------|
| `list(False)` filters `is_active=true` | TC-005 | ✓ |
| `list(True)` returns all | TC-006 | ✓ |
| `soft_delete` preserves row | TC-004/010/014/023/029 | ✓ (sets attr, never deletes) |
| `get` raises NotFoundError on miss | TC-027/028 (via service rewrap) | ✓ (service catches + rewraps with explicit entity string) |
| Repository flushes; service commits | DS-007 boundary | ✓ |

### 4 · Security — PASS

- `select()` — parameterised SQL, no injection surface.
- `session.get(self.model, id_)` — PK lookup, type-enforced.
- `model(**data)`, `setattr(obj, k, v)` — data flows from Pydantic-validated Create/Update schemas in services. Unknown keys silently ignored by SQLAlchemy mapper / become non-persisting instance attrs.
- No raw SQL, shell, FS, or secrets.

### 5 · Structural — PASS

Single class, 5 public methods + ctor + `__class_getitem__`. Inbound edges from T-002 + T-003 (both complete). Outbound edges form when T-006 lands; graphify will then expose 6 entity-specific repo nodes + the finder methods.

---

## Disposition

Mark T-005 `status=complete` in [tasks.json](./tasks.json) and proceed to **`/ases-validate T-006 S1`** (6 entity-specific repos; depends on T-004 + T-005, both now complete).
