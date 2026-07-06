# T-087 tests — services/report_export_service.py (TC-200)

Integration test (format validation fires before any DB call).

| TC | Method | Input | Expected |
|---|---|---|---|
| TC-200 | `export_sales(format='csv', ...)` | format='csv', all other params None | HTTPException 400 |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc200_report_export_service_unsupported_format.py`

See [test_cases.json](../../design/test_cases.json) TC-200 for full inputs/expected_output.
