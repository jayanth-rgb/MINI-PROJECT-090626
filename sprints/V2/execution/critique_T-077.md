# Critique T-077 · InwardReportService · V2 · Iteration 1

**Verdict: CLEAN**  
**File:** `backend/src/application/services/inward_report_service.py`  
**Critiqued:** 2026-07-03 · Issues: 0 critical, 0 major, 0 minor

---

## Lens 1 — Spec ✅ PASS

`generate()` signature matches plan.json and LLD exactly (5 Optional params: `date_from`, `date_to`, `supplier_ids`, `places`, `design_ids`). All four plan steps are implemented:

1. **Shared filter predicate** — `_build_filters()` builds a single `list[ColumnElement[bool]]` from all optional params (DS-017). Neither query method adds inline predicates.
2. **Consolidation query** — `GROUP BY (design_id, design_name, size, grade_id, grade_code)` with `SUM(nos)`, ordered by `design_name ASC, grade_code ASC`. Joins: `tbl_inward_line → tbl_inward_header → tbl_trading_design_master → tbl_grade_master`.
3. **Transactions query** — Per inward line, full context columns, ordered by `purchase_date ASC, header_id ASC`. Joins: `tbl_inward_header → tbl_inward_line → tbl_trading_design_master → tbl_grade_master → tbl_supplier_master`.
4. **Reconciliation assert** — `assert consol_total == txn_total` runs after both queries and before return (DS-017 defense-in-depth). Returns `InwardReportResponse`.

---

## Lens 2 — Contract ✅ PASS

All imports from `depends_on[]` present and used:

| Import | Source | Used for |
|---|---|---|
| `InwardHeaderModel` | `transactions.py` | Join anchor in both queries; purchase_date, supplier_id, place filters |
| `InwardLineModel` | `transactions.py` | Consolidation root table; design_id, grade_id, nos selects + filter |
| `GradeModel` | `master.py` | JOIN on grade_id; grade_code select |
| `SupplierModel` | `master.py` | JOIN on supplier_id (transactions only); supplier_name select |
| `TradingDesignModel` | `master.py` | JOIN on design_id; design_name, size selects |
| `InwardConsolidationRow`, `InwardTransactionRow`, `InwardReportResponse` | `inward_report.py` (T-076) | Schema construction |

ORM column names verified against actual model files — all match:
- `InwardHeaderModel`: `header_id`, `purchase_date`, `supplier_id`, `place` ✅
- `InwardLineModel`: `header_id`, `design_id`, `grade_id`, `nos` ✅
- `TradingDesignModel`: `design_id`, `design_name`, `size` ✅
- `GradeModel`: `grade_id`, `grade_code` ✅
- `SupplierModel`: `supplier_id`, `supplier_name` ✅

**Downstream compatibility:**
- T-087 (`ReportExportService`) calls `InwardReportService(db).generate(**filters)` → return type `InwardReportResponse` matches what T-087 passes to PdfExporter/ExcelExporter.
- T-078 (inward report router) accepts `InwardReportResponse` as its response model → satisfied.

---

## Lens 3 — Test ✅ PASS

**TC-195** (full dataset reconciliation, 3 lines across 2 suppliers/designs):
- No filters → `_build_filters()` returns `[]` → `.where()` no-op → both queries scan full table.
- Consolidation: 3 groups (D1G1=100, D1G2=50, D2G1=75), sum=225.
- Transactions: 3 rows, sum=225. Reconciliation assert passes. ✅

**TC-196** (date filter narrows both sections to July 2 only):
- `_build_filters(date_from=2026-07-02, date_to=2026-07-02)` appends `InwardHeaderModel.purchase_date >= 2026-07-02` and `<= 2026-07-02`.
- Both consolidation (joined to InwardHeaderModel) and transactions (rooted at InwardHeaderModel) share this predicate exactly → only July-2 record (nos=75) appears in both. Reconciliation holds. ✅

**TC-197** (ordering verification):
- Consolidation ORDER BY `TradingDesignModel.design_name ASC` → "12X8 Ridges" (design_id=2) before "16X10 Ridges" (design_id=1). ✅
- Transactions ORDER BY `InwardHeaderModel.purchase_date ASC` → 2026-07-01 row before 2026-07-02 row. ✅

---

## Lens 4 — Security ✅ PASS

- All WHERE predicates use SQLAlchemy parameterized expressions (`Column.in_(list)`, `Column >= value`). No raw SQL string interpolation. No injection vectors.
- **DS-013 compliance:** `places` filter uses `InwardHeaderModel.place.in_(places)` (denormalized snapshot column), not `SupplierModel.place`. `place` SELECT in transactions also reads `InwardHeaderModel.place`. Correct per DS-013.
- **Reconciliation assert (DS-017 ADR tradeoff):** `assert consol_total == txn_total` is disabled under Python `-O` flag. This is the DS-017-mandated defense-in-depth pattern — the same pattern was validated CLEAN in SalesReportService. The shared predicate builder guarantees the invariant by construction; the assert is a future-refactor guard, not primary runtime protection. `is_adr_tradeoff: true`.
- No secrets exposed. No file I/O.

---

## Lens 5 — Structural N/A

`graphify-out/graph.json` exists but was built before T-077's output file was created. `InwardReportService` is not yet in the graph. Router mount (T-078) and `main.py` wiring (T-092) are both pending — reachability from API entry points will be verifiable after those tasks complete. No structural findings at this stage.

---

## ADR Tradeoffs Noted

| ADR | Note |
|---|---|
| DS-017 | `assert` reconciliation check disabled by Python `-O`. Accepted — DS-017 designates this as defense-in-depth for future refactors, not primary validation. Same pattern as validated SalesReportService. |

---

## Positive Observations

- **DS-017 purity:** `_build_filters()` is the sole WHERE source. The private query methods accept only a pre-built filter list and are structurally prevented from introducing predicate drift.
- **DS-013 compliance explicit:** `InwardHeaderModel.place` used for both filter and SELECT projection; `SupplierModel` joined only for `supplier_name`. Module docstring explains the design choice.
- **Correct join roots:** Consolidation roots from `tbl_inward_line` (right anchor for GROUP BY aggregation); transactions roots from `tbl_inward_header` (right anchor for chronological per-line view). Matches SalesReportService pattern.
- **Deterministic secondary sort:** `header_id ASC` as tie-breaker in the transactions query ensures stable ordering when multiple lines share a `purchase_date` — correct robustness beyond the minimum spec.

---

## Next Step

**CLEAN → update tasks.json T-077 status=complete → next task per execution_order.**

Next pending task: T-078 (`inward_report.py` router — depends on T-077 ✅ and T-089).
