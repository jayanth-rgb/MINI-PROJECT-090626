# T-070 tests — repositories/auth.py (TC-185, TC-186)

Integration tests requiring PostgreSQL (testcontainers).

| TC | Method | Setup | Expected |
|---|---|---|---|
| TC-185 | `get_by_username('teststaff')` | Seed user username='teststaff', role='STAFF', is_active=True | Returns UserModel; username='teststaff', role='STAFF', is_active=True |
| TC-186 | `get_by_username('nonexistent_user_xyz_abc')` | No seed | Returns `None` |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc185_user_repository_get_by_username.py`

See [test_cases.json](../../design/test_cases.json) TC-185, TC-186 for full inputs/expected_output.
