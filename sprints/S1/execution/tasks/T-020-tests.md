# T-020 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-035 | AC-011 | Two POST /api/v1/grades with same grade_code -> first 201, second 409 + detail contains "grade_code" |

File: `backend/tests/integration/api/test_grades_api.py`.
