# T-004 — Tests

No dedicated unit tests — ORM models are declarative. Correctness emerges through T-024 (autogenerate produces DDL matching schema.json) and integration tests TC-018, TC-026 (UNIQUE enforcement).

## Manual

```powershell
backend/.venv/Scripts/python.exe -c "from src.infrastructure.db.models.master import SupplierModel; print(len(SupplierModel.__table__.columns))"
# → 5  (supplier_id, supplier_name, place, is_active, created_at)
```

Verify all 6:
```powershell
backend/.venv/Scripts/python.exe -c "from src.infrastructure.db.models.master import SupplierModel, StaffModel, DealerModel, GradeModel, TradingDesignModel, DesignGradeMapModel; print('ok')"
```

## Indirect coverage
- **T-024** — alembic autogenerate produces DDL matching schema.json; reviewer diff
- **TC-018** — duplicate grade_code at DB level → IntegrityError on uq_grade_master_grade_code
- **TC-026** — duplicate (design_id, grade_id) → IntegrityError on uq_design_grade_map_design_grade
