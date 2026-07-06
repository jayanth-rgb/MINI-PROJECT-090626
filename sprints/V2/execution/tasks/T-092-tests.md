# T-092 tests — MODIFY main.py (TC-213)

Integration/system test verifying main.py V2 modifications. Uses fully assembled app (all routers mounted).

| TC | Scenario | Input | Expected |
|---|---|---|---|
| TC-213 | V1 endpoint without auth | GET /dashboard/summary (or any existing V1 route) — no Authorization header | 401 Unauthorized |
| TC-213 smoke | Auth login still open | POST /auth/login with {username: admin, password: admin123} — no Authorization header | 200 (login endpoint unaffected by V2 auth-gating) |

**What TC-213 verifies**: Both assertions together confirm that (a) V1 routes are now auth-gated via `dependencies=[Depends(get_current_user)]` on their include_router calls, and (b) the auth router is correctly mounted without a global dep so login remains publicly accessible.

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc213_main_auth_gate.py`

See [test_cases.json](../../design/test_cases.json) TC-213 for full inputs/expected_output.
