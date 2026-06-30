# Sprint S3 — UI Scaffold Manifest

**Scaffolded:** 2026-06-29 · **Verdict:** **LOCKED** 🔒
**Executed by:** developer agent (Sonnet 4.6) — Gemini fallback in this session

## Build verification

| Check | Command | Exit | Result |
|---|---|:-:|---|
| TypeScript | `npx tsc --noEmit` | **0** | zero errors |
| Next.js build | `npm run build` | **0** | all 15 routes generated |

New routes:
- `/admin/dashboard` — 6.5 kB
- `/admin/reports/sales` — 7.54 kB

## Files created (17 new + 1 modified)

### Types (2)
- `frontend/src/types/dashboard.ts` — `DashboardRow` (16 LOC)
- `frontend/src/types/reports.ts` — `ConsolidationRow`, `TransactionRow`, `SalesReportResponse`, `SalesReportFilters` (39 LOC)

### Integration boundary (2 — locked except for function bodies)
- `frontend/src/lib/api/dashboard.ts` — **IP-S3-001** `getDashboard(asOfDate)` (34 LOC)
- `frontend/src/lib/api/reports.ts` — **IP-S3-002** `getSalesReport(filters)` (100 LOC)

### Pages (2 — server components with `<Suspense>` wrappers per Next.js 15)
- `frontend/src/app/admin/dashboard/page.tsx` (36 LOC)
- `frontend/src/app/admin/reports/sales/page.tsx` (37 LOC)

### Components (11 — locked)
| File | LOC | Notes |
|---|---:|---|
| `components/admin/dashboard/DashboardView.tsx` | 108 | URL-synced asOfDate, react-query, toast on error |
| `components/admin/dashboard/DashboardDatePicker.tsx` | 28 | reuses shadcn calendar (TD-001 patch in place) |
| `components/admin/dashboard/DashboardTable.tsx` | 108 | 8 cols, sticky col 1 mobile, tabular-nums |
| `components/admin/dashboard/EmptyDashboardState.tsx` | 26 | CTA link to /admin/design-grade-map |
| `components/admin/reports/SalesReportView.tsx` | 192 | URL-sync, derived places, ONE badge per page |
| `components/admin/reports/SalesReportFilterBar.tsx` | 169 | Draft state, Apply batches, Reset clears+emits |
| `components/ui/MultiSelectCombobox.tsx` | 218 | + `MultiSelectComboboxFallback` native-select shim for jsdom (TD-010 closure) |
| `components/admin/reports/ConsolidationTable.tsx` | 104 | 4 cols, footer total |
| `components/admin/reports/TransactionsTable.tsx` | 124 | 7 cols, Place + Size hidden on mobile |
| `components/admin/reports/ReconciliationBadge.tsx` | 36 | aria-live='polite', green/red states |
| `components/admin/reports/EmptyReportState.tsx` | 29 | onClear button, aria-labeled |

### Mocks extension (1 — modified)
- `frontend/src/lib/mocks.ts` — appended `MOCK_DASHBOARD_ROWS` (6 rows) + `MOCK_SALES_REPORT_ROWS` (7 rows); existing S1+S2 exports byte-identical.

## Integration points (the ONLY edits allowed after lock)

### IP-S3-001 · `lib/api/dashboard.ts::getDashboard(asOfDate)`
- **Now**: returns mock data filtered by asOfDate
- **After integration**: `apiClient.get('/dashboard', { params: { as_of_date: asOfDate } }).then(r => r.data)`

### IP-S3-002 · `lib/api/reports.ts::getSalesReport(filters)`
- **Now**: applies filters client-side against MOCK_SALES + MOCK_SALES_REPORT_ROWS; verifies AC-050 reconciliation
- **After integration**: build `URLSearchParams.append()` (repeat-key) → `apiClient.get('/reports/sales', { params }).then(r => r.data)`
- ⚠ **Critical**: MUST use `URLSearchParams.append()` or axios `paramsSerializer` for repeat-key list serialization (`?dealer_ids=1&dealer_ids=2`). Comma-joined values fail FastAPI's native list parser. The file header comment includes the exact replacement code.

## Review warnings — all honored at scaffold time

| ID | Resolution evidence |
|---|---|
| **UR-S3-001** | All imports use `Dealer`/`Design` frontend type names — no `DealerRead`/`TradingDesignRead` references |
| **UR-S3-002** | `SalesReportView` derives places via `[...new Set(dealers.map(d => d.place))].sort()` |
| **UR-S3-003** | One `<ReconciliationBadge />` in SalesReportView near FilterBar — not duplicated in section headers |
| **UR-S3-004** | `filtersToSearchParams()` helper skips undefined/empty fields; Reset passes empty params to `router.replace` |

## Tech debt status
- **TD-001** — no new action needed (existing calendar patch unchanged; DashboardDatePicker reuses it)
- **TD-010** — closure path provided: `MultiSelectComboboxFallback` (native select shim) for jsdom tests. The 7 deferred S2 frontend TCs can now be tested when `/ases-test-impl S3` (UI track) runs.

## Deviations from spec (non-blocking)
| Deviation | Rationale |
|---|---|
| No shadcn `Alert` component | Not installed; used inline `<div role='alert'>` with destructive classes. Functionally identical. |
| `<Suspense>` wrappers on pages | Next.js 15 platform requirement for `useSearchParams()` callers. Not a design change. |
| Footer colspan via CSS duplication | Avoids JS colspan-arithmetic bugs when mobile hides 2 columns. |

## Responsive + a11y implemented

**Breakpoints**: mobile < 640 (overflow-x-auto, sticky col 1, Sheet drawer) · tablet 640-1023 (2-col grid) · desktop ≥ 1024 (single row + flex-wrap, sticky filter bar).

**A11y**: keyboard-nav, `aria-live='polite'` on badge, `aria-label` on all buttons/inputs, semantic `<section>/<h1>/<h2>/<table>` landmarks, `tabular-nums` on numeric cells.

## Lock policy 🔒

After this step:
- **Locked**: 17 components + 2 pages + 2 types files + `mocks.ts` content (no rewrites — only deletes after full integration)
- **Unlockable**: 2 function bodies — `getDashboard` and `getSalesReport` — during `/ases-dev S3` integration pass
- **Structural change**: requires a NEW ui-design → ui-review → ui-scaffold cycle

## Next options

1. **`/ases-dev S3`** integration pass — swap the 2 api wrappers from mocks to real `apiClient` calls (estimated: 1-line change per function + URLSearchParams helper for the lists). After this, the running Next.js dev server hits the real backend at `/api/v1/dashboard` + `/api/v1/reports/sales`.
2. **`/ases-test-impl S3` (UI track)** — author the frontend TCs for the 11 new components.
3. Wrap as a separate post-release deliverable and resume V2 scoping.

The pipeline pauses here until you pick a direction.
