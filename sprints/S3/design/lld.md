# Sprint S3 — LLD (Stock Dashboard + Sales Report + Carry-Forward verification)

**Produced:** 2026-06-23 · **Modules:** M-004 (Stock Dashboard), M-005 (Sales Reporting)
**Reuses from S2:** M-003 (domain.stock) · `tbl_stock_ledger` + `ix_stock_ledger_dgt` index · advisory-lock-first DS-002 (now DS-015)
**Reuses from S1:** all 6 master tables + DesignGradeMap

## Sprint goal

Deliver the **read side** of the system. Two user-facing screens:

1. **Stock Dashboard** — `/admin/dashboard/` — Opening / Inward / Outward / Adjust / Closing per (active design, active grade) as of a chosen date, with monthly Opening auto-carrying from previous-month Closing (FORMULA-002).
2. **Sales Report** — `/admin/reports/sales/` — Consolidation (GROUP BY design+grade) + Transaction (per-line) dual-pane with multi-select optional filters: date range, dealer, place, design.

**F-012 Monthly Carry-Forward** is verified by integration tests against the existing `domain.stock.opening_balance` primitive (built in S2 T-045) — no new code paths.

## File roster (10 files, 7 new + 3 modify)

| # | Path | Type | Module | Responsibility |
|---|---|---|---|---|
| 1 | `presentation/schemas/dashboard.py` | create | M-004 | `DashboardRow` Pydantic schema |
| 2 | `infrastructure/db/repositories/ledger_aggregates.py` | create | M-004 | `LedgerAggregatesRepository.sum_deltas_by_source_type` — single CASE-GROUP BY query |
| 3 | `application/services/dashboard_service.py` | create | M-004 | `DashboardService.list_as_of` — compose pairs + opening + closing + aggregates |
| 4 | `presentation/api/routers/dashboard.py` | create | M-004 | GET /api/v1/dashboard |
| 5 | `presentation/schemas/sales_report.py` | create | M-005 | `ConsolidationRow`, `TransactionRow`, `SalesReportResponse` |
| 6 | `application/services/sales_report_service.py` | create | M-005 | `SalesReportService.generate` — single shared filter predicate (DS-017) |
| 7 | `presentation/api/routers/sales_report.py` | create | M-005 | GET /api/v1/reports/sales |
| 8 | `infrastructure/db/repositories/master.py` | **modify** | M-001 | Add `DesignGradeMapRepository.list_active_all` (1 new method) |
| 9 | `presentation/api/dependencies.py` | **modify** | M-002 | Add 2 DI factories (existing 10 untouched) |
| 10 | `main.py` | **modify** | M-002 | Mount 2 new routers under /api/v1 |

## Architecture overview

### Stock Dashboard query strategy (DS-016)

```sql
-- Single CASE-aggregated GROUP BY (covers Inward/Outward/Adjust)
SELECT design_id, grade_id,
  SUM(CASE WHEN source_type='inward'     THEN delta ELSE 0 END) AS inward_sum,
  SUM(CASE WHEN source_type='sale'       THEN -delta ELSE 0 END) AS outward_sum,
  SUM(CASE WHEN source_type='adjustment' THEN delta ELSE 0 END) AS adjust_sum
FROM tbl_stock_ledger
WHERE txn_date BETWEEN :month_start AND :as_of_date
GROUP BY design_id, grade_id;
```

Then **per (active design, active grade) pair**:
- `opening = stock.opening_balance(design_id, grade_id, month_first)` → O(1) latest_as_of (DS-004)
- `closing = stock.closing_balance(design_id, grade_id, as_of_date)` → O(1) latest_as_of (DS-003)
- `inward/outward/adjust` → from the aggregate row dict (default 0)
- **Invariant asserted:** `opening + inward − outward + adjust == closing` (defense-in-depth)

### Sales Report dual-payload strategy (DS-017)

One **shared filter predicate** built once per request, applied to BOTH queries:

```python
def build_filter(date_from, date_to, dealer_ids, places, design_ids):
    conds = []
    if date_from: conds.append(SalesHeader.sales_date >= date_from)
    if date_to:   conds.append(SalesHeader.sales_date <= date_to)
    if dealer_ids: conds.append(SalesHeader.dealer_id.in_(dealer_ids))
    if places:    conds.append(SalesHeader.place.in_(places))
    if design_ids: conds.append(SalesLine.design_id.in_(design_ids))
    return conds
```

- **Consolidation query** — GROUP BY `(design_id, grade_id, design_name, size, grade_code)`, SUM(nos), ORDER BY design_name ASC, grade_code ASC (RULE-019).
- **Transactions query** — per-line projection joined to dealer + design + grade, ORDER BY sales_date ASC (RULE-020).
- **AC-050 reconciliation** — both queries share `build_filter()` output ⇒ identical row set ⇒ sum(transactions.nos) ≡ sum(consolidation.total_nos) **by construction**. Service asserts the invariant defensively before return.

## New decisions (3)

### DS-015 — Amend DS-002 to mandate advisory-lock-first pattern
Closes FA-S2-002/003 + RI-003 from S2 final audit. The verified safe pattern in `domain.stock._apply` is now spec-text: `pg_advisory_xact_lock(design_id, grade_id) → SELECT ... LIMIT 1 FOR UPDATE → insert`. Documents the lesson from TD-011.

### DS-016 — Single GROUP BY for dashboard aggregation
Per-pair sub-queries would not meet AC-045's sub-second target. Single CASE-aggregated SUM over the date window uses `ix_stock_ledger_dgt` for the index range scan; opening/closing remain O(1) per pair via DS-003/004.

### DS-017 — Shared filter predicate for sales report
Single `build_filter()` function feeds both consolidation + transactions queries ⇒ AC-050 invariant holds by construction.

## What's NOT in this LLD (frontend UI track)

Per the S2 precedent, the 2 user-facing pages (`/admin/dashboard/`, `/admin/reports/sales/`) and their dependencies (TS types, axios wrappers, date-range picker, multi-select filter components, optional charting) ship via the UI track: `/ases-ui-design S3` → `/ases-ui-review S3` → `/ases-ui-scaffold S3`. The UI track consumes the API contracts defined above.

## Integration points the UI track will need

- `GET /api/v1/dashboard?as_of_date=`
- `GET /api/v1/reports/sales?date_from=&date_to=&dealer_ids=&places=&design_ids=`
- Existing S1 endpoints for filter-dropdown population: `GET /api/v1/designs`, `GET /api/v1/dealers`
- Existing S2 `GET /api/v1/sales` is NOT used by the report (the report queries the tables directly via the service)

## Rules / formulas referenced

| ID | Description |
|---|---|
| FORMULA-001 | Dashboard column math: Opening + Inward − Outward + Adjust = Closing per row |
| FORMULA-002 | opening_balance(m_first) = closing_balance(m_first − 1 day) — DS-004; already in `domain.stock` from S2 |
| FORMULA-003 | closing_balance(d) = `latest_as_of(d).running_balance` — DS-003 |
| FORMULA-004 | Consolidation = GROUP BY (design, grade) with SUM(nos) |
| RULE-018 | All Sales Report filters optional and multi-select |
| RULE-019 | Consolidation ORDER BY design_name, grade_code |
| RULE-020 | Transactions ORDER BY sales_date ASC |
| AC-053 | Carry-forward correct after back-dated cross-month txn — integration test only |

## Depends on completed sprints

- **S1** (M-001) — all 6 master CRUD + DesignGradeMap + master ORM models
- **S2** (M-003 + M-007) — `domain.stock.{opening_balance, closing_balance, apply_*}`, `tbl_stock_ledger`, `ix_stock_ledger_dgt` composite index

## Next

→ `/ases-schema S3`
