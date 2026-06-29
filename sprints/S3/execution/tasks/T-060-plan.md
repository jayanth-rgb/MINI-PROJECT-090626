# T-060 — `infrastructure/db/repositories/master.py` MODIFY — list_active_all

**Module:** M-001 · **Depends on:** — (Group A) · **DS:** DS-007

## Context anchor
Adds a sibling method to the existing `DesignGradeMapRepository.list_active_by_design` (S1, file:46). T-061 (DashboardService) needs **all** active `(design, grade)` pairs across the whole catalogue — `list_active_by_design` requires a `design_id` and would force one call per design (N+1).

Existing surface of `DesignGradeMapRepository`:
```python
class DesignGradeMapRepository(BaseRepository[DesignGradeMapModel]):
    def get_by_pair(self, design_id: int, grade_id: int) -> DesignGradeMapModel | None: ...
    def list_active_by_design(self, design_id: int) -> list[DesignGradeMapModel]: ...
```

This task appends `list_active_all()`. Six other repositories in the same file (`SupplierRepository`, `StaffRepository`, `DealerRepository`, `GradeRepository`, `TradingDesignRepository`) **must not be touched**.

## Implementation logic

```python
# Appended to backend/src/infrastructure/db/repositories/master.py, inside DesignGradeMapRepository:

    def list_active_all(self) -> list[DesignGradeMapModel]:
        # AC-012/AC-017: grade-soft-delete + map-soft-delete BOTH cascade — JOIN on
        # tbl_grade_master with grade.is_active=True (DS-007).
        stmt = (
            select(DesignGradeMapModel)
            .join(GradeModel, GradeModel.grade_id == DesignGradeMapModel.grade_id)
            .where(
                DesignGradeMapModel.is_active.is_(True),
                GradeModel.is_active.is_(True),
            )
        )
        return list(self.session.execute(stmt).scalars())
```

> The `.design` and `.grade` relationships on `DesignGradeMapModel` are declared `lazy='joined'` in S1, so the scalar load eager-fetches both — no N+1 in T-061's downstream projection.

## Constraints
- Append-only edit; existing methods byte-identical.
- Same JOIN-on-grade pattern as `list_active_by_design` (no shortcut via `DesignGradeMapModel.is_active` alone — AC-012 requires the grade-side cascade).
- No new imports — `select`, `DesignGradeMapModel`, `GradeModel` already imported at the top of the file.
- Returns `list[DesignGradeMapModel]` (not raw `Row`), so downstream code can access `.design.design_name`, `.design.size`, `.grade.grade_code`.

## Do not touch
- `SupplierRepository`, `StaffRepository`, `DealerRepository`, `GradeRepository`, `TradingDesignRepository` (all in the same file)
- Existing methods `get_by_pair`, `list_active_by_design`
- Any other file in the repo (including model files)

## Success criteria
- **Manual**: `git diff` shows only the new method body appended. Seed 3 active pairs + 1 deactivated map + 1 deactivated grade → `list_active_all()` returns exactly 3 rows.
- **Automated**: TC-150 + TC-151 + TC-152 pass.
- **DoD**: New method uses `select(DesignGradeMapModel).join(GradeModel, ...).where(map.is_active, grade.is_active)`. No design-id filter. Existing code unchanged.

## Checkout
> *"DesignGradeMapRepository.list_active_all appended. JOIN-on-grade preserves AC-012/AC-017 cascade. Ready for DashboardService row-set enumeration in T-061."*
