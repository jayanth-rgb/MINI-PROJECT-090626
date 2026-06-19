# T-017 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-033 | AC-001 | POST /api/v1/suppliers returns 201 + SupplierRead body; row persists |
| TC-034 | AC-002 | DELETE /api/v1/suppliers/{id} returns 200 + body with is_active=false; row physically present |

File: `backend/tests/integration/api/test_suppliers_api.py` (uses TestClient + testcontainers PG via conftest T-009).
