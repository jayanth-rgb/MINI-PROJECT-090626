# Critique — T-015 DesignGradeMapService

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/design_grade_map_service.py` (75 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — service consumes only repository + schemas + domain exceptions
- **DS-008** soft delete only — `deactivate_mapping` uses `repo.soft_delete`, no hard `delete()`
- **DS-012** generic BaseRepository — service composes 3 repositories (mapping + design + grade) for FK validation

## Lens 1 — Spec
LLD `files[12].functions` signature parity:
- `list_mappings(include_inactive: bool = False) -> list[DesignGradeMapRead]` ✓
- `list_active_grades_for_design(design_id: int) -> list[DesignGradeReadMin]` ✓ (DF-006 contract, AC-019)
- `create_mapping(payload: DesignGradeMapCreate) -> DesignGradeMapRead` raises `NotFoundError`, `ConflictError` ✓
- `update_mapping(map_id: int, patch: DesignGradeMapUpdate) -> DesignGradeMapRead` raises `NotFoundError` (via repo) ✓
- `deactivate_mapping(map_id: int) -> DesignGradeMapRead` raises `NotFoundError` (via repo) ✓

The private `_hydrate` staticmethod is an internal refactor of the 4× repeated `DesignGradeMapRead(...)` construction that appears literally in `plan.md`. It does not alter any public signature, is not exported, does not leave the file, and does not appear in `LLD.interfaces.exports`. Not flagged — scope of the rule "no new functions" is exported/cross-file functions, not within-class private helpers.

## Lens 2 — Contract
Imports vs `depends_on = ["T-006", "T-007", "T-003"]`:
- T-006 → `DesignGradeMapRepository`, `TradingDesignRepository`, `GradeRepository` (all in master.py) ✓
- T-007 → `DesignGradeMapCreate/Update/Read`, `DesignGradeReadMin` ✓
- T-003 → `ConflictError`, `NotFoundError` ✓

Repository methods exercised exist:
- `repo.list_active_by_design(design_id)` — confirmed at `master.py:46` (filters both `map.is_active` and `grade.is_active`)
- `repo.get_by_pair(design_id, grade_id)` — confirmed at `master.py:38`
- Base methods `list/get/create/update/soft_delete` — confirmed in `base.py`

Exports: class `DesignGradeMapService` matches LLD `interfaces.exports` ✓.

## Lens 3 — Test (7/7 covered)
- **TC-024** (AC-016, create happy): design_repo.get + grade_repo.get + get_by_pair=None + create + commit + reload + hydrate → returns row with `is_active=true` ✓
- **TC-025** (AC-016, duplicate pair): `ConflictError` message is `"(design_id, grade_id) = (10, 1) already exists"` — substring `"design_id, grade_id"` present per `error_message_contains` ✓
- **TC-027** (AC-016, bad design FK): `try design_repo.get(99999) except NotFoundError → raise NotFoundError("TradingDesign", 99999)`; instance `.entity == "TradingDesign"` ✓
- **TC-028** (AC-016, bad grade FK): design_repo.get(10) succeeds; `try grade_repo.get(99999) except NotFoundError → raise NotFoundError("Grade", 99999)`; `.entity == "Grade"` ✓
- **TC-029** (AC-017, soft delete): `repo.soft_delete(5)` sets `is_active=False`, flush+commit, row preserved (DS-008) ✓
- **TC-031** (AC-019, active projection): `list_active_grades_for_design(10)` → repo applies map+grade `is_active` filter via JOIN → projected as `DesignGradeReadMin(grade_id, grade_code)` ✓
- **TC-032** (AC-019, empty): no mappings for design_id=20 → repo returns `[]` → empty list returned (no error) ✓

## Lens 4 — Security
- All persistence through ORM repository methods — parameterized, no SQL injection vectors ✓
- `DesignGradeMapCreate` enforces `design_id: int = Field(gt=0)`, `grade_id: int = Field(gt=0)` at presentation boundary; values are cast to int by Pydantic before reaching the service ✓
- `ConflictError` message embeds the int IDs only — no string interpolation of user-controllable text ✓
- FK pre-check (`design_repo.get` / `grade_repo.get`) prevents leaking IntegrityError details from a downstream FK violation; explicit `NotFoundError` keeps the 404 mapping deterministic ✓

## Lens 5 — Structural
- Imported by `dependencies.py` (T-016) — `get_design_grade_map_service` ✓
- Consumed by `designs.py` router (T-021) for `GET /designs/{id}/grades` (DF-006) ✓
- Consumed by `design_grade_map.py` router (T-022) for admin CRUD ✓
- All public methods reachable from at least one route ✓

## Verdict
**CLEAN** — no issues across spec / contract / test / security / structural lenses. The invariant-heavy service satisfies all 7 listed test cases by construction. Proceed.
