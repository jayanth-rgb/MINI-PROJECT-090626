# T-035 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-039 | AC-001 | Submit SupplierForm with supplier_name='' -> inline 'required' error; onSubmit NOT called |
| TC-040 | AC-002 | Deactivate button calls DELETE /suppliers/{id}; row renders muted after refetch |

Files:
- `frontend/src/components/admin/suppliers/__tests__/SupplierForm.test.tsx`
- `frontend/src/app/admin/suppliers/__tests__/page.test.tsx`
