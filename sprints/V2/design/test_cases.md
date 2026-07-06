# V2 Test Case Specifications

**Sprint:** V2  
**Produced by:** `/ases-test-spec V2`  
**TC range:** TC-171 – TC-217 (47 test cases)  
**Prior ranges:** S1 TC-001..TC-046 · S2 TC-047..TC-114 · S3 TC-115..TC-170

---

## V2 Acceptance Criteria (LLD-synthesized — no PRD update filed)

| AC | Feature | Criterion |
|----|---------|-----------|
| AC-054 | F-013 | POST /auth/login valid credentials → 200 TokenResponse (access_token, token_type='bearer', role) |
| AC-055 | F-013 | POST /auth/login wrong password / unknown user → 401 |
| AC-056 | F-013 | POST /auth/login deactivated user (is_active=false) → 401 |
| AC-057 | F-014 | GET /auth/me valid Bearer → 200 UserRead |
| AC-058 | F-014 | All V1+V2 endpoints except /auth/login require Bearer token; unauthenticated → 401 |
| AC-059 | F-014 | require_supervisor guard → 403 for STAFF/VERIFIER; SUPERVISOR passes |
| AC-060 | F-014 | SUPERVISOR can POST /users (201) and PATCH /users/{id} (200) |
| AC-061 | F-015 | GET /reports/inward no filters → all data; sum(transactions.nos)==sum(consolidation.total_nos) |
| AC-062 | F-015 | Multi-select filters narrow both consolidation + transactions via identical predicate |
| AC-063 | F-015 | Consolidation ordered design_name ASC, grade_code ASC; transactions ordered purchase_date ASC |
| AC-064 | F-016 | GET /reports/sales/export?format=pdf → 200 application/pdf with %PDF- magic bytes |
| AC-065 | F-016 | GET /reports/inward/export?format=xlsx → 200 XLSX MIME with 2-sheet workbook |
| AC-066 | F-016 | Unsupported format → 400 |
| AC-067 | F-017 | Duplicate (design_id, grade_id, effective_from) price → 409 |
| AC-068 | F-017 | Active price lookup: most recent effective_from ≤ today; None → unit_price=0 fallback |
| AC-069 | F-018 | POST /invoices → invoice_number=INV-YYYYMMDD-NNNNN, total_amount=Σ line_totals, status=PENDING |
| AC-070 | F-018 | Second invoice for same sales_header_id → 409 |
| AC-071 | F-018 | Invoice line unit_price is immutable snapshot; price master edits don't retroact |
| AC-072 | F-019 | POST /invoices/{id}/payments → status recomputed (PENDING→PARTIAL or PAID) |
| AC-073 | F-019 | Overpayment → 422 |
| AC-074 | DS-020 | Concurrent first-row tbl_stock_ledger inserts serialized by advisory lock; running_balance=50+30=80, 0 errors (TD-008) |

---

## Coverage Summary

| Feature | ACs | Covered | TC IDs |
|---------|-----|---------|--------|
| F-013 Auth | 3 | 3 | TC-171..TC-175, TC-185..TC-186, TC-190..TC-192, TC-208..TC-209 |
| F-014 RBAC | 4 | 4 | TC-193..TC-194, TC-210..TC-213 |
| F-015 Inward Report | 3 | 3 | TC-195..TC-197, TC-214 |
| F-016 Export | 3 | 3 | TC-198..TC-200, TC-215..TC-216 |
| F-017 Price Master | 2 | 2 | TC-187..TC-188, TC-201 |
| F-018 Invoicing | 3 | 3 | TC-176..TC-184, TC-189, TC-202..TC-204, TC-217 |
| F-019 Payments | 2 | 2 | TC-181..TC-183, TC-205..TC-206 |
| DS-020 TD-008 | 1 | 1 | TC-207 |

---

## Test Cases by Module

### M-008: Auth & RBAC — domain/auth.py (unit)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-171 | AC-054 | verify_password: correct hash → True | unit | critical |
| TC-172 | AC-055 | verify_password: wrong password → False | edge | critical |
| TC-173 | AC-054 | create_access_token: payload contains sub + role + future exp | unit | critical |
| TC-174 | AC-055 | decode_access_token: expired token → None | edge | critical |
| TC-175 | AC-055 | decode_access_token: malformed token → None | edge | critical |

### M-011: Invoicing — domain/invoice.py (unit)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-176 | AC-069 | compute_line_total: 10 × 150.00 = 1500.00 | unit | critical |
| TC-177 | AC-069 | compute_line_total: quantity=0 → ValueError | edge | critical |
| TC-178 | AC-069 | compute_line_total: unit_price=-10.00 → ValueError | edge | critical |
| TC-179 | AC-069 | compute_invoice_total: [100, 200.50, 50.25] = 350.75 | unit | critical |
| TC-180 | AC-069 | compute_invoice_total: empty list → ValueError | edge | high |
| TC-181 | AC-072 | compute_invoice_status: paid=[] → PENDING | unit | critical |
| TC-182 | AC-072 | compute_invoice_status: paid=400/1000 → PARTIAL | unit | critical |
| TC-183 | AC-072 | compute_invoice_status: paid=600+400/1000 → PAID | unit | critical |
| TC-184 | AC-069 | generate_invoice_number: (2026-07-02, 42) → INV-20260702-00042 | unit | critical |

### M-008: Auth — repositories/auth.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-185 | AC-054 | UserRepository.get_by_username: found → UserModel | integration | critical |
| TC-186 | AC-055 | UserRepository.get_by_username: not found → None | edge | critical |

### M-011: Pricing — repositories/pricing.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-187 | AC-068 | get_active_price: 2 rows → returns effective_from=2026-06-01 (most recent) | integration | critical |
| TC-188 | AC-068 | get_active_price: only inactive row → None | edge | critical |
| TC-189 | AC-069 | create_with_lines: atomic header + 1 line; eager-loaded result | integration | critical |

### M-008: Auth — services/auth_service.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-190 | AC-054 | authenticate: valid → TokenResponse role=SUPERVISOR | integration | critical |
| TC-191 | AC-055 | authenticate: wrong password → HTTPException 401 | integration | critical |
| TC-192 | AC-056 | authenticate: is_active=false → HTTPException 401 | integration | critical |
| TC-193 | AC-057 | get_current_user: valid token → UserModel | integration | critical |
| TC-194 | AC-060 | create_user: duplicate username → HTTPException 409 | edge | critical |

### M-009: Inward Report — services/inward_report_service.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-195 | AC-061 | generate() no filters: 3 lines, reconciliation sum=225 holds | integration | critical |
| TC-196 | AC-062 | generate() date filter: 1 line returned, reconciliation holds | integration | critical |
| TC-197 | AC-063 | generate() ordering: consolidation by design_name ASC; transactions by purchase_date ASC | integration | critical |

### M-010: Exporters — infrastructure (unit)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-198 | AC-064 | PdfExporter.export_sales_report: BytesIO starts with %PDF- | unit | critical |
| TC-199 | AC-065 | ExcelExporter.export_inward_report: 2-sheet XLSX (Consolidation + Transactions) | unit | critical |
| TC-200 | AC-066 | ReportExportService.export_sales: format=csv → HTTPException 400 | edge | high |

### M-011: Pricing — services/pricing_service.py (integration/edge)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-201 | AC-067 | create_price: duplicate (design,grade,effective_from) → HTTPException 409 | edge | critical |

### M-011: Invoicing — services/invoice_service.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-202 | AC-069 | create_from_sales: 2 lines, total=1400.00, unit_price snapshotted | integration | critical |
| TC-203 | AC-070 | create_from_sales: already invoiced → HTTPException 409 | edge | critical |
| TC-204 | AC-071 | create_from_sales: price update after creation doesn't alter invoice line | integration | high |
| TC-205 | AC-072 | record_payment: full payment → status=PAID | integration | critical |
| TC-206 | AC-073 | record_payment: overpayment (400+200 > 500) → HTTPException 422 | edge | critical |

### DS-020 / TD-008 Coverage — domain/stock.py (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-207 | AC-074 | Concurrent first-row stock ledger insert: advisory lock serializes, running_balance=80 | integration | critical |

### M-008: Auth — API routers (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-208 | AC-054 | POST /auth/login valid → 200 TokenResponse | integration | critical |
| TC-209 | AC-055 | POST /auth/login wrong password → 401 | integration | critical |
| TC-210 | AC-057 | GET /auth/me valid Bearer → 200 UserRead | integration | critical |
| TC-211 | AC-059 | GET /users STAFF Bearer → 403 | integration | critical |
| TC-212 | AC-060 | POST /users SUPERVISOR → 201 UserRead | integration | critical |
| TC-213 | AC-058 | GET /suppliers without Bearer → 401 (V1 endpoint global guard) | integration | critical |

### M-009 + M-010: Report API routers (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-214 | AC-061 | GET /reports/inward authenticated → 200 InwardReportResponse | integration | critical |
| TC-215 | AC-064 | GET /reports/sales/export?format=pdf → 200 application/pdf | integration | critical |
| TC-216 | AC-065 | GET /reports/inward/export?format=xlsx → 200 XLSX MIME | integration | critical |

### M-011: Invoice API router (integration)

| ID | AC | Description | Type | Priority |
|----|----|-------------|------|----------|
| TC-217 | AC-069 | POST /invoices SUPERVISOR → 201 InvoiceRead, total=1800.00, status=PENDING | integration | critical |

---

## Framework and File Mapping

All 47 test cases use **pytest** (FastAPI TestClient for router tests, SQLAlchemy test session for integration tests).

| Layer | Files | Test Type |
|-------|-------|-----------|
| domain/auth.py | TC-171..TC-175 | pure unit (no DB) |
| domain/invoice.py | TC-176..TC-184 | pure unit (no DB) |
| repositories/auth.py | TC-185..TC-186 | integration (real DB) |
| repositories/pricing.py | TC-187..TC-189 | integration (real DB) |
| services/auth_service.py | TC-190..TC-194 | integration (real DB) |
| services/inward_report_service.py | TC-195..TC-197 | integration (real DB) |
| exporters/pdf + excel | TC-198..TC-199 | unit (no DB, in-memory) |
| services/report_export_service.py | TC-200 | edge (mock sub-services) |
| services/pricing_service.py | TC-201 | integration (real DB) |
| services/invoice_service.py | TC-202..TC-206 | integration (real DB) |
| domain/stock.py (TD-008) | TC-207 | integration (real DB, 2 threads) |
| routers/auth.py, users.py | TC-208..TC-213 | integration (TestClient + DB) |
| routers/inward_report.py, report_export.py | TC-214..TC-216 | integration (TestClient + DB) |
| routers/invoices.py | TC-217 | integration (TestClient + DB) |

---

## Next Step
→ `/ases-sprint-gate V2`
