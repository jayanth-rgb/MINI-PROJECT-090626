# T-013 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-017 | AC-011 | create_grade with duplicate grade_code → ConflictError("grade_code 'X' already exists") |
| TC-019 | AC-012 | deactivate_grade interlocks with DesignGradeMapService.list_active_grades_for_design — verified via TC-019 setup (cross-service) |

File: `backend/tests/unit/application/services/test_grade_service.py`
Run: `pytest backend/tests/unit/application/services/test_grade_service.py -v`

> TC-019 spans GradeService + DesignGradeMapService; the test setup seeds a grade in both states, then asserts the JOIN filter in `list_active_grades_for_design` excludes the inactive one.
