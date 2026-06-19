# Sprint S1 — Test Case Specifications

**Produced by:** `/ases-test-spec S1`
**Sprint:** S1 — Master Data Foundation
**Companion JSON:** [test_cases.json](./test_cases.json)
**Inputs:** [contracts/prd.json](../../../contracts/prd.json), [lld.json](./lld.json), [schema.json](./schema.json)

> **Specs only.** Implementation comes in Phase 3 (`/ases-test-impl`). Every case below has deterministic `inputs` and `expected_output` so the implementer has no degrees of freedom.

---

## 1. Headline numbers

| Metric | Value |
|--------|------:|
| Features in scope | **6** (F-001 … F-006) |
| Acceptance criteria covered | **19 / 19** |
| Test cases authored | **46** |
| Critical priority | **30** |
| High priority | **16** |
| Edge / negative cases | **15** |
| Backend (pytest)   | **38** |
| Frontend (jest)    | **8** |
| Playwright (E2E)   | 0 — deferred to Phase 3 |

**Rule checked at gate:** every test case links to a real `ac_ref` from `prd.json` (rule 10 of CLAUDE.md). No invented criteria.

---

## 2. AC ↔ Test coverage matrix

| AC | Feature | Test IDs | Type mix |
|----|---------|----------|----------|
| AC-001 | F-001 Supplier name+place required | TC-001, TC-002, TC-003, TC-033, TC-039 | unit + edge + integration + frontend |
| AC-002 | F-001 Soft-delete + hidden from dropdown | TC-004, TC-005, TC-006, TC-034, TC-040 | unit + integration + frontend |
| AC-003 | F-001 Seed 3 suppliers | TC-007 | unit |
| AC-004 | F-002 Staff name required | TC-008, TC-009, TC-041 | unit + edge + frontend |
| AC-005 | F-002 Soft-delete staff | TC-010 | unit |
| AC-006 | F-002 Seed 9 staff | TC-011 | unit |
| AC-007 | F-003 Dealer name+place required | TC-012, TC-013, TC-042 | unit + edge + frontend |
| AC-008 | F-003 Soft-delete dealer | TC-014 | unit |
| AC-009 | F-003 Seed 3 dealers | TC-015 | unit |
| AC-010 | F-004 Seed 9 grade codes | TC-016 | unit |
| AC-011 | F-004 UNIQUE(grade_code) | TC-017, TC-018, TC-035, TC-043 | unit + integration (DB) + integration (API) + frontend |
| AC-012 | F-004 Deactivate grade removes it from combinations | TC-019 | unit |
| AC-013 | F-005 Design size+name required | TC-020, TC-021, TC-044 | unit + edge + frontend |
| AC-014 | F-005 Seed 3 designs | TC-022 | unit |
| AC-015 | F-005 Soft-delete design | TC-023 | unit |
| AC-016 | F-006 UNIQUE(design_id, grade_id) + FK exists | TC-024, TC-025, TC-026, TC-027, TC-028, TC-038, TC-045, TC-046 | unit + edge + integration (DB) + integration (API) + frontend |
| AC-017 | F-006 Deactivate mapping; transactions unaffected | TC-029 | unit |
| AC-018 | F-006 Seed 6 mappings | TC-030 | unit |
| AC-019 | F-006 GET /designs/{id}/grades active-only | TC-031, TC-032, TC-036, TC-037 | unit + edge + integration |

---

## 3. Coverage by layer

```
Backend
├── unit (services + schemas + seed)        24 cases — TC-001..023 + TC-024, TC-025, TC-027..032
├── integration (DB constraints)             2 cases — TC-018, TC-026
└── integration (API contracts)              6 cases — TC-033..038

Frontend
└── unit (form + page-level)                 8 cases — TC-039..046
```

---

## 4. Highlighted test cases — verbatim from JSON

### 4.1 TC-001 · AC-001 · happy path
```yaml
function:  SupplierService.create_supplier
input:     { supplier_name: "Manjunatha", place: "Mallur" }
output:    { supplier_id: 1, supplier_name: "Manjunatha", place: "Mallur", is_active: true }
side_fx:   INSERT INTO tbl_supplier_master (1 row); session committed
raises:    —
framework: pytest
```

### 4.2 TC-018 · AC-011 · schema-level UNIQUE
```yaml
function:  tbl_grade_master.UNIQUE(grade_code)
inputs:
  first_insert:  { grade_code: "DIM" }
  second_insert: { grade_code: "DIM" }
expected:  second_insert_violates_constraint = uq_grade_master_grade_code
raises:    sqlalchemy.exc.IntegrityError
framework: pytest (integration / real test DB)
```

> Pairs with **TC-017** (service-level pre-check raises `ConflictError`) and **TC-035** (HTTP returns 409). Together they prove the constraint holds end-to-end at three layers.

### 4.3 TC-036 · AC-019 · the DF-006 contract S2 depends on
```yaml
endpoint:   GET /api/v1/designs/{design_id}/grades
seed:
  design_id 10 with grades 1 (active) and 2 (active),
  mappings: (10,1) active, (10,2) inactive
expected:   status=200, body=[{ grade_id: 1, grade_code: "1" }], body_item_keys_exact=[grade_id, grade_code]
framework:  pytest (integration / FastAPI TestClient)
```

> This is the contract every S2 transaction form will JOIN against. If this test breaks, S2 cannot ship.

### 4.4 TC-019 · AC-012 · interlocking grade deactivation
```yaml
function:  DesignGradeMapService.list_active_grades_for_design
setup:     grade 2 is_active=false; mapping (10, 2) is_active=true; mapping (10, 1) is_active=true
query:     design_id=10
expected:  [{ grade_id: 1, grade_code: "1" }]  (only count=1)
```

> Verifies that the JOIN filter on `g.is_active=true` excludes the mapping even though the mapping row itself is still active. Catches a class of bug where the implementer filters only on `m.is_active`.

---

## 5. Edge / negative cases (explicit per rule)

| TC | AC | Negative scenario |
|----|----|-------------------|
| TC-002 | AC-001 | Empty `supplier_name` rejected at Pydantic |
| TC-003 | AC-001 | Empty `place` rejected at Pydantic |
| TC-009 | AC-004 | Empty `staff_name` rejected |
| TC-013 | AC-007 | Empty `dealer_name` OR empty `place` rejected (parameterised) |
| TC-017 | AC-011 | Duplicate `grade_code` → `ConflictError` (service layer) |
| TC-018 | AC-011 | Duplicate `grade_code` → `IntegrityError` (DB layer) |
| TC-021 | AC-013 | Empty `size` OR empty `design_name` rejected |
| TC-025 | AC-016 | Duplicate `(design_id, grade_id)` → `ConflictError` |
| TC-026 | AC-016 | Duplicate `(design_id, grade_id)` → `IntegrityError` (DB) |
| TC-027 | AC-016 | Non-existent `design_id` → `NotFoundError` |
| TC-028 | AC-016 | Non-existent `grade_id` → `NotFoundError` |
| TC-032 | AC-019 | Design with zero active mappings returns `[]` (no error) — critical for ERR-012 in S2 Adjustment form |
| TC-037 | AC-019 | Same case at HTTP layer — 200 + `[]` |
| TC-042 | AC-007 | DealerForm rejects empty name or place (UI) |
| TC-046 | AC-016 | DesignGradeMapForm rejects unselected dropdowns (UI) |

---

## 6. What is intentionally NOT tested in S1

| Area | Why | Future home |
|------|-----|-------------|
| Performance / dashboard latency (AC-045) | No dashboard in S1 | `/ases-system-test S3` |
| Authentication / RBAC | V1 ships open-network per DS-005 | V2 sprint |
| Playwright E2E flows | First UI shipped in S1 has no transactional flow yet | `/ases-integration-test` + `/ases-system-test` in Phase 3 |
| Concurrency / SELECT FOR UPDATE (DS-002) | No stock ledger writes in S1 | S2 / S3 |
| Carry-forward correctness (AC-051..053) | No `tbl_stock_ledger` in S1 | S3 |
| Stock dashboard NFR | S3 feature | S3 |

These deferrals are documented in `open_items_for_sprint_gate` inside `test_cases.json` so `/ases-sprint-gate S1` can ack them without re-deriving the reasoning.

---

## 7. Mapping to LLD test_required: true files

Every LLD file with `test_required: true` has at least one test case that exercises it:

| LLD file | Covered by |
|----------|-----------|
| `backend/src/config.py` | indirectly via TC-033..038 (TestClient requires settings) |
| `backend/src/infrastructure/db/session.py` | TC-005, TC-006 (uses real session against in-memory or test DB) |
| `backend/src/infrastructure/db/models/master.py` | TC-018, TC-026 (DDL exercised) |
| `backend/src/infrastructure/db/repositories/base.py` + `master.py` | TC-005..006, TC-017, TC-019, TC-031..032 |
| `backend/src/application/services/*` (6 files) | TC-001, TC-004..006, TC-008, TC-010, TC-012, TC-014, TC-017, TC-019, TC-020, TC-023, TC-024..029, TC-031..032 |
| `backend/src/presentation/schemas/master.py` | TC-002, TC-003, TC-009, TC-013, TC-021 |
| `backend/src/presentation/api/errors.py` | TC-034, TC-035, TC-038 (exercised via the 409/200 mapping) |
| `backend/src/presentation/api/routers/*` (6 files) | TC-033..038 |
| `backend/src/main.py` | TC-033..038 (TestClient boot) |
| `backend/scripts/seed_master_data.py` | TC-007, TC-011, TC-015, TC-016, TC-022, TC-030 |
| `frontend/src/lib/api/masters.ts` | TC-040, TC-043, TC-045 (mocked) |
| `frontend/src/components/admin/MasterDataTable.tsx` | TC-040 |
| `frontend/src/components/admin/MasterFormDialog.tsx` | TC-040, TC-043, TC-045 (wraps the form submits) |
| `frontend/src/app/admin/<entity>/page.tsx` (6 pages) | TC-040, TC-043, TC-045 (sampled — staff/dealers/designs follow same shape) |
| `frontend/src/components/admin/<entity>/<Entity>Form.tsx` (6 forms) | TC-039, TC-041, TC-042, TC-044, TC-046 |

> The 6 admin pages share the same shape. Per ASES rule 1 (testable AC) + rule 10 (no invented cases), redundant identical tests are *not* duplicated for each entity — the shared `MasterDataTable` + `MasterFormDialog` are tested once and the per-entity wiring is sampled.

---

## 8. Acceptance gate

`/ases-sprint-gate S1` will verify:

- [x] All 19 ACs covered
- [x] Every test case has `ac_ref`
- [x] No invented criteria
- [x] Inputs + expected_output are deterministic (concrete values, not "any string")
- [x] Edge cases explicitly typed `edge`
- [x] Framework specified per case
- [x] `test_cases.json` validates against `format/json/test_cases.schema.json`

---

## 9. Next Step

→ **`/ases-sprint-gate S1`** — the determinism gate. Runs five consistency checks across `prd.json`, `hld.json`, `lld.json`, `schema.json`, `test_cases.json`. PO must approve PASS before `/ases-analyze`.
