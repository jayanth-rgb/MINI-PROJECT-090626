# T-010 — Critique

**Produced by:** `/ases-critique T-010 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-010.json](./critique_T-010.json)
**Reviewed file:** [backend/src/application/services/supplier_service.py](../../../backend/src/application/services/supplier_service.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 4 methods match LLD `files[7]` |
| Contract | **PASS** — T-016 + T-017 satisfied |
| Test | **PASS** — TC-001/004/005/006 supported |
| Security | **PASS** — Pydantic-validated input, parameterised SQL, no read-path commits |
| Structural | PASS |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

Sets the canonical pattern T-011..T-014 will mirror.

---

## Decisions consulted (M-001)

DS-007 (layering — service calls repo, not raw SQL), DS-008 (soft delete via `repo.soft_delete`), DS-012 (single persistence path through `BaseRepository[SupplierModel]`). All satisfied.

---

## Lens-by-lens

### 1 · Spec — PASS

| Method | Behaviour |
|--------|-----------|
| `list_suppliers(include_inactive=False)` | `repo.list(...)` → `[SupplierRead.model_validate(r) for r in rows]` — no commit |
| `create_supplier(payload)` | `repo.create(payload.model_dump())` → `session.commit()` → `SupplierRead.model_validate(obj)` |
| `update_supplier(id, patch)` | `repo.update(id, patch.model_dump(exclude_none=True))` → commit → Read |
| `deactivate_supplier(id)` | `repo.soft_delete(id)` → commit → Read |

Service-owned commit pattern (writes only); read path is idempotent.

### 2 · Contract — PASS

| Downstream | Uses | OK? |
|-----------|------|-----|
| T-016 `dependencies.get_supplier_service` | `SupplierService(db)` ctor | ✓ |
| T-017 router | `service.{list,create,update,deactivate}_supplier` | ✓ |

All imports used: `Session`, `SupplierRepository`, 3 schemas.

### 3 · Test — PASS

| TC | Mechanism |
|----|-----------|
| TC-001 | `payload.model_dump()` → `repo.create` → commit → `SupplierRead.model_validate(obj)` returns DB-assigned id + `is_active=True` |
| TC-004 | `repo.soft_delete` (DS-008) sets `is_active=False`; row preserved |
| TC-005 | `include_inactive=False` → `repo.list` filters via `is_active.is_(True)` |
| TC-006 | `include_inactive=True` → no filter; both rows returned |

Edge cases handled:
- `exclude_none=True` on patch dump → partial update skips unset fields.
- `repo.update` / `repo.soft_delete` raise `NotFoundError`; service propagates → T-008 mapper → 404.
- `session.commit()` failure → propagates → `get_db` rolls back (T-002).

### 4 · Security — PASS

- Pydantic validates upstream (T-007: `min_length=1` on required fields).
- All DB access via parameterised SQLAlchemy — no injection.
- `exclude_none=True` prevents accidental field nulling.
- Read path doesn't commit → no unintended mutations.

### 5 · Structural — PASS

Single class, 1 ctor + 4 methods. Inbound: T-006, T-007 ✓. Outbound: T-016, T-017.

---

## Disposition

Mark T-010 `status=complete` in [tasks.json](./tasks.json) and proceed to **`/ases-validate T-011 S1`** (StaffService — same pattern; depends on the same complete set).
