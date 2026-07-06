# T-083 tests — services/pricing_service.py (TC-201)

Integration test requiring PostgreSQL (testcontainers).

| TC | Method | Setup | Expected |
|---|---|---|---|
| TC-201 | `create_price(data)` | Seed price row (design_id=1, grade_id=1, effective_from=2026-07-01, unit_price=100.00) | create_price with same (design_id=1, grade_id=1, effective_from=2026-07-01, unit_price=150.00) → HTTPException 409 |

**Test file location** (implemented at /ases-test-impl V2): `backend/tests/integration/test_tc201_pricing_service_duplicate_price_409.py`

See [test_cases.json](../../design/test_cases.json) TC-201 for full inputs/expected_output.
