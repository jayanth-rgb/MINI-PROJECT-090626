# T-077 tests — services/inward_report_service.py (TC-195..TC-197)

Integration tests requiring PostgreSQL (testcontainers).

| TC | Scenario | Filters | Expected |
|---|---|---|---|
| TC-195 | 3 inward lines, 2 suppliers, 2 designs | None | sum(nos)=225 in both sections; 3 transactions, 3 consolidation rows; reconciliation holds |
| TC-196 | 2 lines on different dates (Jul 1 + Jul 2) | date_from=2026-07-02, date_to=2026-07-02 | 1 transaction (Jul 2 only, nos=75); consolidation total_nos=75; reconciliation holds |
| TC-197 | 2 designs: '16X10 Ridges' + '12X8 Ridges' | None | consolidation[0].design_name='12X8 Ridges' (ASC); transactions[0].purchase_date=2026-07-01 (ASC) |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc195_inward_report_service_reconciliation.py` etc.

See [test_cases.json](../../design/test_cases.json) TC-195..TC-197 for full seed data and expected_output.
