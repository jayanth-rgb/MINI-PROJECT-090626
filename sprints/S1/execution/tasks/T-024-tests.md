# T-024 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-018 | AC-011 | INSERT duplicate grade_code raises IntegrityError citing uq_grade_master_grade_code |
| TC-026 | AC-016 | INSERT duplicate (design_id, grade_id) raises IntegrityError citing uq_design_grade_map_design_grade |

Files:
- `backend/tests/integration/db/test_grade_master_unique.py`
- `backend/tests/integration/db/test_design_grade_map_unique.py`

> Both run against testcontainers-PG from T-009 conftest with the migration applied at fixture setup.
