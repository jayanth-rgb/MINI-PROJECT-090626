# T-006 — Per-entity Repositories

**Module:** M-001 · **Depends on:** T-004, T-005 · **TC refs:** indirect

## Implementation logic

```python
# backend/src/infrastructure/db/repositories/master.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.db.models.master import (
    SupplierModel, StaffModel, DealerModel, GradeModel,
    TradingDesignModel, DesignGradeMapModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[SupplierModel]):
    pass


class StaffRepository(BaseRepository[StaffModel]):
    pass


class DealerRepository(BaseRepository[DealerModel]):
    pass


class GradeRepository(BaseRepository[GradeModel]):
    def get_by_code(self, code: str) -> GradeModel | None:
        return self.session.execute(select(GradeModel).where(GradeModel.grade_code == code)).scalar_one_or_none()


class TradingDesignRepository(BaseRepository[TradingDesignModel]):
    pass


class DesignGradeMapRepository(BaseRepository[DesignGradeMapModel]):
    def get_by_pair(self, design_id: int, grade_id: int) -> DesignGradeMapModel | None:
        return self.session.execute(
            select(DesignGradeMapModel).where(
                DesignGradeMapModel.design_id == design_id,
                DesignGradeMapModel.grade_id == grade_id,
            )
        ).scalar_one_or_none()

    def list_active_by_design(self, design_id: int) -> list[DesignGradeMapModel]:
        # AC-019: active mappings only AND grade.is_active=true (the JOIN filter)
        stmt = (
            select(DesignGradeMapModel)
            .join(GradeModel, GradeModel.grade_id == DesignGradeMapModel.grade_id)
            .where(
                DesignGradeMapModel.design_id == design_id,
                DesignGradeMapModel.is_active.is_(True),
                GradeModel.is_active.is_(True),
            )
        )
        return list(self.session.execute(stmt).scalars())
```

## Constraints
- DS-012: BaseRepository is the access pattern; services never construct SQL
- AC-019 (key invariant tested by TC-019): list_active_by_design MUST filter BOTH map.is_active AND grade.is_active
- AC-011 (TC-017): get_by_code is the pre-check finder
- AC-016 (TC-025): get_by_pair is the pre-check finder

## Do not touch
Any other file.

## Success criteria
- **Manual:** `python -c "from src.infrastructure.db.repositories.master import SupplierRepository, StaffRepository, DealerRepository, GradeRepository, TradingDesignRepository, DesignGradeMapRepository; print(hasattr(GradeRepository, 'get_by_code'), hasattr(DesignGradeMapRepository, 'list_active_by_design'))"` → `True True`
- **Automated:** via TC-017, TC-019, TC-024..028, TC-031, TC-032
- **DoD:** 6 subclasses; 3 finders; no SQL outside this file

## Checkout prompt
*"6 master repositories created. GradeRepository.get_by_code + DesignGradeMapRepository.get_by_pair + list_active_by_design added."*
