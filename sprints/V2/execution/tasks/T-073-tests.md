# T-073 tests — routers/users.py (TC-211..TC-212)

Integration tests using FastAPI TestClient + testcontainers PostgreSQL.

| TC | Endpoint | Token role | Input body | Expected |
|---|---|---|---|---|
| TC-211 | POST /users | SUPERVISOR (admin) | {username: 'newstaff', password: 'pass1234', role: 'STAFF'} | 201; id is positive int; role='STAFF'; is_active=True |
| TC-212 | POST /users | STAFF (created in setup) | {username: 'another', password: 'pass1234', role: 'STAFF'} | 403 |

**Setup note for TC-212**: Seed admin via T-075, create a STAFF user via POST /users (as SUPERVISOR), log in as STAFF user to obtain STAFF JWT, then attempt POST /users as STAFF.

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc211_users_router_supervisor_create.py`

See [test_cases.json](../../design/test_cases.json) TC-211..TC-212 for full inputs/expected_output.
