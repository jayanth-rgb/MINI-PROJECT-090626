# T-015 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-024 | AC-016 | create_mapping happy path |
| TC-025 | AC-016 | duplicate (design_id, grade_id) → ConflictError |
| TC-027 | AC-016 | non-existent design_id → NotFoundError("TradingDesign", id) |
| TC-028 | AC-016 | non-existent grade_id → NotFoundError("Grade", id) |
| TC-029 | AC-017 | deactivate_mapping — row preserved |
| TC-031 | AC-019 | list_active_grades_for_design returns active projection |
| TC-032 | AC-019 | design with no active mappings → empty list |

File: `backend/tests/unit/application/services/test_design_grade_map_service.py`

> 7 test cases — the densest file in the suite. Also feeds TC-019 (which sets up cross-service inactive grade + active mapping).
