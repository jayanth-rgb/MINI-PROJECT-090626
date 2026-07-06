# T-068 tests — domain/auth.py (TC-171..TC-175)

All unit tests. No DB required.

| TC | Function | Input | Expected |
|---|---|---|---|
| TC-171 | `verify_password` | plain='admin123', hashed=get_password_hash('admin123') | `True` |
| TC-172 | `verify_password` | plain='wrongpassword', hashed=get_password_hash('admin123') | `False` |
| TC-173 | `create_access_token` | data={'sub':'admin','role':'SUPERVISOR'}, expires_delta=28800s | decoded payload has sub='admin', role='SUPERVISOR', exp in future |
| TC-174 | `decode_access_token` | token created with expires_delta=timedelta(seconds=-1) | `None` |
| TC-175 | `decode_access_token` | token='not.a.valid.jwt.string' | `None` |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/unit/test_tc171_verify_password_match.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-171..TC-175 for full inputs/expected_output.
