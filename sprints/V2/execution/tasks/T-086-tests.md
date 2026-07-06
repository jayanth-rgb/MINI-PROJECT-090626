# T-086 tests — exporters/excel_exporter.py (TC-199)

Unit test. No DB required.

| TC | Method | Input | Expected |
|---|---|---|---|
| TC-199 | `export_inward_report(data, {})` | InwardReportResponse with 1 consolidation + 1 transaction row | `wb.sheetnames == ['Consolidation', 'Transactions']`; `len(wb.sheetnames) == 2` |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/unit/test_tc199_excel_exporter_inward_sheet_names.py`

See [test_cases.json](../../design/test_cases.json) TC-199 for full inputs/expected_output.
