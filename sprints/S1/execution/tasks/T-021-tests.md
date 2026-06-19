# T-021 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-036 | AC-019 | GET /designs/{id}/grades returns 200 with [{grade_id, grade_code}] for active mappings only |
| TC-037 | AC-019 | GET /designs/{id}/grades for a design with no active mappings returns 200 + [] |

File: `backend/tests/integration/api/test_designs_grades_api.py`.
