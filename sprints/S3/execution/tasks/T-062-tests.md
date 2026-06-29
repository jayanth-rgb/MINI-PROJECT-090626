# T-062 tests — 14 TCs (covers all F-011 ACs incl. AC-050 reconciliation)

| TC | Type/Priority | AC | Asserts |
|----|---|---|---|
| TC-133 | integration/critical | AC-046 | No filters → full dataset returned (RULE-018). |
| TC-134 | integration/critical | AC-046 | `date_from + date_to` only → window-filtered rows. |
| TC-135 | integration/critical | AC-046 | `dealer_ids=[a,b]` → only sales with header.dealer_id ∈ {a,b}. |
| TC-136 | integration/critical | AC-046 | `places=["X","Y"]` → only sales with header.place_snapshot ∈ {X,Y} (DS-013). |
| TC-137 | integration/critical | AC-047 | Consolidation rows GROUP BY (design_id, grade_id) with SUM(nos) per group. |
| TC-138 | integration/critical | AC-047 | Consolidation ORDER BY design_name ASC, grade_code ASC (RULE-019). |
| TC-139 | integration/critical | AC-048 | Transactions ORDER BY sales_date ASC, header_id ASC (RULE-020). |
| **TC-141** | **integration/critical** | **AC-050** | **No filters → sum(transactions.nos) == sum(consolidation.total_nos).** |
| **TC-142** | **integration/critical** | **AC-050** | **All 5 filters set simultaneously → reconciliation still holds.** |
| TC-143 | unit/critical | AC-046 | `_build_filters` with all-None inputs returns empty list (full dataset). |
| TC-144 | edge/high | AC-046 | `_build_filters` with empty list inputs (e.g. `dealer_ids=[]`) treats them as "no filter" — does NOT generate `IN ()`. |
| **TC-145** | **edge/high** | **AC-050** | **Filter combination that yields zero rows: both lists empty + reconciliation holds (0 == 0).** |
| TC-146 | unit/high | AC-047 | `_query_consolidation` returns objects validating against ConsolidationRow schema. |
| **TC-157** | **performance/high** | **AC-046** | **p95 < 1500ms over 10 runs with 6 dealers × 12 months × 50 sales/month dataset.** |

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.

> Integration tests live in `backend/tests/integration/api/test_sales_report_api.py`; unit tests for `_build_filters` and the projection shape live in `backend/tests/unit/application/services/test_sales_report_service.py`. Authored at `/ases-test-impl S3`.
