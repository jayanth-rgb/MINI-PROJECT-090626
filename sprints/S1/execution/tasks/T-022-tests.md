# T-022 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-038 | AC-016 | POST /design-grade-map with duplicate (design_id, grade_id) returns 409 + detail contains "design_id, grade_id" |

File: `backend/tests/integration/api/test_design_grade_map_api.py`.
