# Sprint S3 — UI Spec

**Designed:** 2026-06-29 · **Scope features:** F-010 Stock Dashboard, F-011 Sales Report · **F-012:** verification-only, no UI surface.

> Designer note: drafted by Opus running the `/ases-ui-design` role because no Gemini agent is available in this Claude Code session. Spec is platform-neutral and re-runnable.

## Stack
Next.js 15.1 App Router · React 19 · shadcn/ui (radix-nova preset) · Tailwind · @tanstack/react-query · axios (via existing `lib/api/client.ts`) · zod · sonner.

## Routes
| Path | Page | Feature |
|---|---|---|
| `/admin/dashboard` | `DashboardPage` | F-010 |
| `/admin/reports/sales` | `SalesReportPage` | F-011 |

## Integration boundary
Two new wrapper modules sit between components and the backend, mirroring the S2 `lib/api/transactions.ts` pattern:

| File | Function | Initial impl (scaffold) | Integration impl (devops) |
|---|---|---|---|
| `lib/api/dashboard.ts` | `getDashboard(asOfDate)` | reads `MOCK_DASHBOARD_ROWS` and filters | `apiClient.get('/dashboard', { params: { as_of_date: asOfDate } })` |
| `lib/api/reports.ts` | `getSalesReport(filters)` | reads `MOCK_SALES` and applies filters client-side | `apiClient.get('/reports/sales', { params: <repeat-key serializer> })` |

⚠ **Critical for `getSalesReport`**: axios must serialize list params as repeat-key (`?dealer_ids=1&dealer_ids=2`), NOT comma-joined. FastAPI's native list parsing depends on this. Use `paramsSerializer` or `URLSearchParams`.

## New types
- `types/dashboard.ts` — `DashboardRow` (10 fields matching the backend Pydantic schema)
- `types/reports.ts` — `ConsolidationRow`, `TransactionRow`, `SalesReportResponse`, `SalesReportFilters`

## Components (11 total)

| Component | Role | File |
|---|---|---|
| **DashboardPage** | Server-component page | `app/admin/dashboard/page.tsx` |
| **DashboardView** | Client container · owns asOfDate state · URL-synced | `components/admin/dashboard/DashboardView.tsx` |
| **DashboardDatePicker** | Single-date picker (reuses shadcn calendar with TD-001 patch) | `components/admin/dashboard/DashboardDatePicker.tsx` |
| **DashboardTable** | 10-column data table · server-sorted · skeleton on load | `components/admin/dashboard/DashboardTable.tsx` |
| **EmptyDashboardState** | "No active pairs" CTA → `/admin/design-grade-map` | `components/admin/dashboard/EmptyDashboardState.tsx` |
| **SalesReportPage** | Server-component page | `app/admin/reports/sales/page.tsx` |
| **SalesReportView** | Client container · 5-filter state · URL-synced · dual-payload render per AC-049 | `components/admin/reports/SalesReportView.tsx` |
| **SalesReportFilterBar** | 5 controls · batched Apply (avoids per-keystroke refetch) · Reset | `components/admin/reports/SalesReportFilterBar.tsx` |
| **MultiSelectCombobox** *(reusable)* | shadcn-style multi-select with chip pills · closes TD-010 via native-select test shim | `components/ui/MultiSelectCombobox.tsx` |
| **ConsolidationTable** | 4-column grouped table · footer total | `components/admin/reports/ConsolidationTable.tsx` |
| **TransactionsTable** | 7-column transaction list · footer total | `components/admin/reports/TransactionsTable.tsx` |
| **ReconciliationBadge** | Visible AC-050 client-side verifier (server already asserts) | `components/admin/reports/ReconciliationBadge.tsx` |
| **EmptyReportState** | "No sales match filters" + Clear-filters button | `components/admin/reports/EmptyReportState.tsx` |

## AC-049 layout (both sections on the same screen)
```
+--------------------------------------------------+
|  Sales Report                                    |
|  [FilterBar: dateFrom dateTo dealers places designs] [Apply] [Reset]
|                                                  |
|  ╭─ Consolidation ────────── 28 ✓ ────────────╮  |
|  │  Design | Size | Grade | Total Nos         │  |
|  │  ────────────────────────────────────       │  |
|  │  ...                                         │  |
|  ╰──────────────────────────────────────────────╯  |
|                                                  |
|  ╭─ Transactions ───────── 28 ✓ ────────────╮  |
|  │  Date | Dealer | Place | Design | Grade | Nos │  |
|  │  ───────────────────────────────────────────  │  |
|  │  ...                                          │  |
|  ╰───────────────────────────────────────────────╯  |
+--------------------------------------------------+
```
No tabs, no toggle, Consolidation FIRST — per AC-049.

## State + URL sync
- **Dashboard**: `/admin/dashboard?as_of_date=YYYY-MM-DD` — single param, defaults to today.
- **Sales Report**: `/admin/reports/sales?date_from=&date_to=&dealer_ids=1&dealer_ids=2&places=Mysuru&design_ids=...` — all optional, multi-select via repeat keys.

React Query keys:
```
['dashboard', asOfDate]
['sales-report', JSON.stringify(filters)]
['dealers']  // S1
['designs']  // S1
```

## Responsive
| Breakpoint | Behavior |
|---|---|
| **mobile** (< 640px) | Tables wrap in `overflow-x-auto`; column 1 sticky. FilterBar collapses to a "Filters (N active)" Sheet/Drawer trigger. Cards stack. |
| **tablet** (640–1023px) | FilterBar arranges in a 2-column grid; tables fill container; chips wrap. |
| **desktop** (≥ 1024px) | FilterBar single row + flex-wrap; tables natural width; sticky FilterBar at top of content area. |

## A11y
- Forms keyboard-navigable (PRD `non_functional.accessibility`)
- Tab order: date picker / filter bar → tables
- All numeric cells right-aligned + `tabular-nums`
- `aria-live='polite'` on `ReconciliationBadge` so screen readers announce changes after filter updates
- `<section aria-labelledby='consolidation-h'><h2 id='consolidation-h'>...` semantic landmarks
- shadcn radix-nova defaults meet WCAG AA color contrast

## Loading + error
- **Loading**: react-query `isLoading` drives shadcn `<Skeleton />` rows (6 dashboard, 10 reports).
- **Empty**: render only when `!isLoading && rows.length === 0` — specific component per page.
- **Error**: shared `<ErrorState />` from S1 + sonner toast with the message; retry button calls `queryClient.refetchQueries`.

## Tech debt addressed
- **TD-001** — shadcn calendar patch already in place from `/ases-scaffold`; both date pickers reuse the existing component.
- **TD-010** — `MultiSelectCombobox` is designed with a thin native `<select multiple>` jsdom shim path so the deferred 7 frontend TCs from S2 can be tested.

## Future (V2 / out of S3 scope)
- Pagination on `/reports/sales` (currently returns full filtered set)
- CSV/PDF export
- Chart panel on dashboard (table-only ships in S3)
- Date-range picker on dashboard (single date in V1)

## Next
`/ases-ui-review S3` — Opus validates this spec against PRD ACs + HLD module boundaries.
