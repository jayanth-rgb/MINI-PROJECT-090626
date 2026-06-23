# Sprint S2 — Test Case Specifications

**Sprint:** S2 · **Features:** F-007, F-008, F-009 · **ACs:** 21 (AC-020..AC-040)
**Total TCs:** 56 (TC-047..TC-102; numbering continues from S1)
**Framework split:** pytest 43, jest 13, playwright 0 (deferred)

## TCs per feature

| Feature | Range | Count |
|---------|-------|-------|
| F-007 Inward (AC-020..AC-027) | TC-047..TC-057 (+ shared stock-ledger TCs 79, 83, 86, 87, 88, 89; + frontend TC-090..TC-095) | 22 |
| F-008 Sales (AC-028..AC-033) | TC-058..TC-066 (+ TC-084; + TC-096, TC-097) | 12 |
| F-009 Adjustment (AC-034..AC-040) | TC-067..TC-078 (+ TC-080..TC-082, TC-085; + TC-098..TC-102) | 22 |

(Some stock-ledger TCs serve multiple features — see coverage matrix.)

## AC coverage matrix

All 21 ACs covered by ≥1 test case; the heaviest concentrations:
- **AC-027** (atomic header+lines+ledger save) — 8 TCs across service, domain, DB, API, concurrency
- **AC-036** (software_cb pre-populate from ledger) — 3 TCs across service, API, frontend
- **AC-039** (adjustment ledger write) — 3 TCs across service, API, domain

## Test file structure

### Backend
```
backend/tests/unit/application/services/
  test_inward_service.py           # AC-020..AC-027 service-layer tests
  test_sales_service.py            # AC-028..AC-033
  test_adjustment_service.py       # AC-034..AC-040
  test_design_grade_cb_service.py  # AC-036 (GET /designs/{id}/grades-with-cb)
backend/tests/unit/presentation/schemas/
  test_transactions_schemas.py     # All Pydantic edge cases (nos<=0, physical_cb<0, stock_date>entry_date, required fields)
backend/tests/unit/domain/
  test_stock.py                    # apply_inward/sale/adjustment, closing_balance, opening_balance, back-date forward-recompute
backend/tests/integration/db/
  test_transaction_constraints.py  # All DB-level CHECKs + FK RESTRICT
  test_stock_ledger_concurrency.py # SELECT FOR UPDATE serialization (DS-002)
backend/tests/integration/api/
  test_inward_api.py
  test_sales_api.py
  test_adjustments_api.py
  test_designs_grades_with_cb_api.py
```

### Frontend
```
frontend/src/components/transactions/inward/__tests__/InwardForm.test.tsx
frontend/src/components/transactions/sales/__tests__/SalesForm.test.tsx
frontend/src/components/transactions/adjustment/__tests__/AdjustmentForm.test.tsx
```

Frontend file paths assume the UI scaffold step lays out `src/components/transactions/{inward,sales,adjustment}/` with the form components colocated with their tests — same pattern as S1's admin forms.

## Highest-risk tests (worth extra critique attention)

| TC | Why |
|----|-----|
| **TC-086** | Back-dated transaction forward-recompute — touches every later row of the same (design, grade). HLD R-003 mitigation. Critical to S3 reporting correctness. |
| **TC-087** | Concurrent-write SELECT FOR UPDATE serialization — HLD R-001 mitigation (DS-002). Requires careful pytest fixture (likely `threading.Thread` + `Barrier` against two separate sessions on the same engine). |
| **TC-070, TC-071** | Software_cb pre-population — Adjustment form's behavior pivots on the closing_balance projection being correct as of stock_date. Drives whether `difference` is meaningful. |

## Open items for `/ases-sprint-gate S2`

1. **AC-045 perf NFR** still S3 (no change from S1 deferral).
2. **TC-087 concurrency fixture** — implementation strategy will be refined in `/ases-test-impl S2`. Either two-thread pytest with a Barrier, or a custom session-pair fixture.
3. **TC-086 back-date recompute** — single TC but covers the highest-risk logic; recommend a dedicated `/ases-critique` pass even at spec stage.
4. **Frontend directory structure** for `transactions/{inward,sales,adjustment}/` assumed — UI scaffold step (`/ases-ui-design S2 → /ases-ui-scaffold S2`) will materialize.

## Completeness

| Check | Result |
|-------|--------|
| Every AC has ≥1 test | ✓ 21/21 |
| Every test has `ac_ref` | ✓ |
| Every test has concrete `inputs` | ✓ |
| Every test has concrete `expected_output` | ✓ |
| Edge cases explicit (`type: edge`) | ✓ |
| No invented test cases | ✓ |

## Next step
→ `/ases-sprint-gate S2` — 5-check consistency verification across lld/schema/test_cases + PRD AC coverage. Must PASS before Phase 2 execution begins.
