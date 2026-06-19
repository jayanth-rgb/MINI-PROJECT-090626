# T-007 — Tests

## Test cases covered (implemented in `/ases-test-impl S1`)

| TC | AC | Schema | Scenario |
|----|----|----|----------|
| TC-002 | AC-001 | SupplierCreate | empty `supplier_name` → ValidationError |
| TC-003 | AC-001 | SupplierCreate | empty `place` → ValidationError |
| TC-009 | AC-004 | StaffCreate | empty `staff_name` → ValidationError |
| TC-013 | AC-007 | DealerCreate | empty dealer_name OR empty place (parameterised) |
| TC-021 | AC-013 | DesignCreate | empty size OR empty design_name (parameterised) |

## Test file location
`backend/tests/unit/presentation/schemas/test_master_schemas.py`

## Run command
```powershell
cd backend
.venv/Scripts/python.exe -m pytest tests/unit/presentation/schemas/test_master_schemas.py -v
```

## Manual smoke
```powershell
backend/.venv/Scripts/python.exe -c "from src.presentation.schemas.master import SupplierCreate; SupplierCreate(supplier_name='', place='X')"
# → pydantic.ValidationError: 1 validation error for SupplierCreate / supplier_name / String should have at least 1 character
```
