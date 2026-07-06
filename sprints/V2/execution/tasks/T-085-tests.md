# T-085 tests — exporters/pdf_exporter.py (TC-198)

Unit test. No DB required.

| TC | Method | Input | Expected |
|---|---|---|---|
| TC-198 | `export_sales_report(data, {})` | SalesReportResponse with 1 consolidation + 1 transaction row | `buf.read(5) == b'%PDF-'`; `buf.getbuffer().nbytes > 0` |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/unit/test_tc198_pdf_exporter_sales_magic_bytes.py`

See [test_cases.json](../../design/test_cases.json) TC-198 for full inputs/expected_output.
