# T-006 — Tests

No dedicated test file. Each finder is exercised by the service test that needs it.

## Manual

```powershell
backend/.venv/Scripts/python.exe -c "from src.infrastructure.db.repositories.master import GradeRepository, DesignGradeMapRepository; print(hasattr(GradeRepository, 'get_by_code'), hasattr(DesignGradeMapRepository, 'list_active_by_design'))"
# → True True
```

## Indirect coverage
| TC | Verifies |
|----|----------|
| TC-017 | GradeRepository.get_by_code (duplicate raises ConflictError at service layer) |
| TC-019 | DesignGradeMapRepository.list_active_by_design — interlocking grade.is_active filter |
| TC-024, TC-025 | DesignGradeMapRepository.get_by_pair (pre-insert duplicate check) |
| TC-031, TC-032 | list_active_by_design — projection + empty-list case |
