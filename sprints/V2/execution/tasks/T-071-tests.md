# T-071 tests — services/auth_service.py (TC-190..TC-194)

Integration tests requiring PostgreSQL (testcontainers).

| TC | Method | Setup | Expected |
|---|---|---|---|
| TC-190 | `authenticate('admin','admin123')` | Seed admin/admin123/SUPERVISOR/active | TokenResponse: token_type='bearer', role='SUPERVISOR', access_token non-empty |
| TC-191 | `authenticate('admin','wrongpassword')` | Seed admin/admin123/SUPERVISOR | HTTPException 401 |
| TC-192 | `authenticate('inactiveuser','pass123')` | Seed inactiveuser/pass123/STAFF/is_active=False | HTTPException 401 |
| TC-193 | `get_current_user(valid_jwt)` | Seed admin/SUPERVISOR/active; valid JWT for sub='admin' | UserModel: username='admin', role='SUPERVISOR', is_active=True |
| TC-194 | `create_user(UserCreate(username='dupuser',...))` | Seed dupuser/STAFF | HTTPException 409 |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc190_auth_service_authenticate_success.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-190..TC-194 for full inputs/expected_output.
