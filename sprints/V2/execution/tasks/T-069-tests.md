# T-069 tests — none direct

`test_required=false` per LLD. Schema correctness verified transitively:

| Where | TCs | What is asserted |
|---|---|---|
| T-071 (AuthService) | TC-190..TC-194 | TokenResponse deserialized from service; UserRead serialized from UserModel via from_attributes. |
| T-072 (auth router) | TC-208, TC-210 | HTTP response body validates as TokenResponse and UserRead respectively. |
| T-073 (users router) | TC-212 | POST /users response validates as UserRead (status, username, role, is_active). |

See [test_cases.json](../../design/test_cases.json) for full inputs/expected_output.
