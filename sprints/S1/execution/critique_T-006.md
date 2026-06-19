# T-006 — Critique

**Produced by:** `/ases-critique T-006 S1` · **Iteration:** 1/3 · **Verdict:** **CLEAN**
**Companion JSON:** [critique_T-006.json](./critique_T-006.json)
**Reviewed file:** [backend/src/infrastructure/db/repositories/master.py](../../../backend/src/infrastructure/db/repositories/master.py)

---

## Headline

| Lens | Result |
|------|--------|
| Spec | **PASS** — 6 subclasses + 3 finders match LLD `files[5]` |
| Contract | **PASS** — all 6 services (T-010..T-015) satisfied; T-015 cross-repo wiring works |
| Test | **PASS** — TC-017/019/024/025/027/028/031/032 supported |
| Security | **PASS** — parameterised SQL, typed params |
| Structural | PASS — no orphans, clean inbound edges |
| ADR tradeoff? | No |
| Iteration cap | 1/3 |

---

## Decisions consulted (M-001)

DS-007 (layering — services route through repos), DS-012 (generic repository + per-entity finders). All satisfied — no raw SQL outside this file or BaseRepository.

---

## Lens-by-lens

### 1 · Spec — PASS

| Repo | Special methods |
|------|-----------------|
| `SupplierRepository` | inherits CRUD only |
| `StaffRepository` | inherits CRUD only |
| `DealerRepository` | inherits CRUD only |
| `GradeRepository` | + `get_by_code(code) → GradeModel \| None` |
| `TradingDesignRepository` | inherits CRUD only |
| `DesignGradeMapRepository` | + `get_by_pair(design_id, grade_id) → DesignGradeMapModel \| None` <br> + `list_active_by_design(design_id) → list[DesignGradeMapModel]` (JOIN on `GradeModel`, filter `map.is_active AND grade.is_active`) |

**AC-019 invariant** correctly implemented: JOIN to `GradeModel` and filter both `DesignGradeMapModel.is_active.is_(True)` AND `GradeModel.is_active.is_(True)` — required by TC-019.

### 2 · Contract — PASS

| Service | Uses | OK? |
|---------|------|-----|
| T-010 SupplierService | `SupplierRepository` CRUD | ✓ |
| T-011 StaffService | `StaffRepository` CRUD | ✓ |
| T-012 DealerService | `DealerRepository` CRUD | ✓ |
| T-013 GradeService | `GradeRepository.get_by_code` + CRUD | ✓ |
| T-014 DesignService | `TradingDesignRepository` CRUD | ✓ |
| T-015 DesignGradeMapService | `DesignGradeMapRepository.{get_by_pair, list_active_by_design}` + CRUD; `TradingDesignRepository.get`; `GradeRepository.get` | ✓ |

Imports: `sqlalchemy.select` (used by 3 finders), 6 ORM models (T-004), `BaseRepository` (T-005). All used.

### 3 · Test — PASS

| TC | Behaviour | OK? |
|----|-----------|-----|
| TC-017 | `get_by_code('1')` returns existing → service raises `ConflictError` | ✓ |
| TC-019 | After grade deactivate, `list_active_by_design` excludes via `GradeModel.is_active.is_(True)` JOIN clause | ✓ |
| TC-024 | `get_by_pair` returns None → service proceeds with `create` | ✓ |
| TC-025 | `get_by_pair` returns existing → service raises `ConflictError` | ✓ |
| TC-027/028 | `repo.get(id)` (inherited) raises `NotFoundError` on miss; service rewraps with explicit entity string | ✓ |
| TC-031 | `list_active_by_design` JOIN filters: returns only the row with both map+grade active | ✓ |
| TC-032 | No active mappings → JOIN produces empty result → `list()` returns `[]` | ✓ |

### 4 · Security — PASS

All queries use `sqlalchemy.select(...).where(Model.col == value)` — SQLAlchemy binds values as query parameters; no injection surface. Typed `code: str`, `design_id: int`, `grade_id: int` parameters. `scalar_one_or_none()` returns None safely without raising on no-match.

### 5 · Structural — PASS

Single file, 6 sibling classes, 3 added methods. Inbound: `models.master` (T-004), `repositories.base` (T-005) — both complete. Outbound edges materialise as T-010..T-015 land.

---

## Soft notes (non-blocking)

### N-001 · plan.md lists unused `Session` import

`plan.md` line 10 imports `Session` but the file doesn't use it (all session access goes through `self.session` inherited from BaseRepository). Developer correctly omitted it — best practice, no dead imports. Logged so future critique runs don't mistake the omission for drift.

---

## Disposition

Mark T-006 `status=complete` in [tasks.json](./tasks.json) and proceed to **`/ases-validate T-007 S1`** — Pydantic schemas (parallel-group 1, zero deps; required by T-010..T-015 services).
