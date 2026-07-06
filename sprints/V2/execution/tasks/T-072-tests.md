# T-072 tests — routers/auth.py (TC-208..TC-210)

Integration tests using FastAPI TestClient + testcontainers PostgreSQL. Requires seeded admin user (T-075 seed_default_user.py: admin/admin123/SUPERVISOR).

| TC | Endpoint | Input | Expected |
|---|---|---|---|
| TC-208 | POST /auth/login | form: username=admin, password=admin123 | 200; access_token non-empty str; token_type='bearer'; role='SUPERVISOR' |
| TC-209 | POST /auth/login | form: username=admin, password=wrongpassword | 401 |
| TC-210 | GET /auth/me | Authorization: Bearer \<token from TC-208\> | 200; username='admin'; role='SUPERVISOR'; is_active=True |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc208_auth_router_login.py`

See [test_cases.json](../../design/test_cases.json) TC-208..TC-210 for full inputs/expected_output.
