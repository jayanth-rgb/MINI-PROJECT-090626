# T-060 tests — 3 TCs (1 unit + 2 cascade-edge)

| TC | Type/Priority | Asserts |
|----|---|---|
| TC-150 | unit/critical | Basic listing: 3 active pairs across 2 designs (all grades active) → list_active_all returns exactly 3 rows; `.design.size` and `.grade.grade_code` populated via lazy='joined'. |
| TC-151 | edge/critical | **AC-017 cascade** — a (design, grade) pair with `map.is_active=False` is excluded even if its grade is active. |
| TC-152 | edge/critical | **AC-012 cascade** — a (design, grade) pair with `map.is_active=True` but `grade.is_active=False` is excluded. |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> Tests live in `backend/tests/integration/db/test_design_grade_map_list_active_all.py` at `/ases-test-impl S3` time (testcontainers-backed integration tests).
