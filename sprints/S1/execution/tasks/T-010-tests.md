# T-010 — Tests

| TC | AC | Scenario |
|----|----|----|
| TC-001 | AC-001 | create_supplier happy path |
| TC-004 | AC-002 | deactivate_supplier sets is_active=false, row preserved |
| TC-005 | AC-002 | list_suppliers default excludes is_active=false |
| TC-006 | AC-002 | list_suppliers(include_inactive=True) returns both |

File: `backend/tests/unit/application/services/test_supplier_service.py`

Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/application/services/test_supplier_service.py -v`

Uses fixtures from T-009 (`db_session`).
