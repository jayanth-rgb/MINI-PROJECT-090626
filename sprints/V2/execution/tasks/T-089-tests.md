# T-089 tests — MODIFY dependencies.py

No dedicated TCs. Auth guard behavior verified transitively by router integration tests.

| Verified via | TC | What is asserted |
|---|---|---|
| T-072 auth router | TC-208 | Valid login -> 200 (oauth2_scheme + get_current_user pathway exercised) |
| T-073 users router | TC-212 | STAFF token on SUPERVISOR endpoint -> 403 (require_supervisor blocks) |
| T-092 main.py test | TC-213 | Existing V1 endpoint without token -> 401 (get_current_user on V1 mounts) |

**Test file location**: No standalone test file — covered by router integration tests above.
