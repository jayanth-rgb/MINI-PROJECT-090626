# T-025 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-007 | AC-003 | seed_suppliers — 3 rows, idempotent on re-run |
| TC-011 | AC-006 | seed_staff — 9 rows, exact names per AC-006 |
| TC-015 | AC-009 | seed_dealers — 3 rows |
| TC-016 | AC-010 | seed_grades — 9 grade codes |
| TC-022 | AC-014 | seed_designs — 3 size/name pairs |
| TC-030 | AC-018 | seed_design_grade_map — 6 combinations resolved by natural key |

File: `backend/tests/unit/scripts/test_seed_master_data.py` — each test runs the seeder twice and asserts the final row count matches expected and the second run inserts zero rows.
