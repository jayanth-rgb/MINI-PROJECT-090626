# Sprint S3 — UI Review

**Reviewed:** 2026-06-29 · **Reviewer:** Critic (Opus) · **Verdict:** **APPROVED** ✅

## Three-check summary

| Check | Status | Highlight |
|---|---|---|
| **AC coverage** | PASS | 10/13 UI-related ACs map to ≥1 component; 3 are correctly UI-less (F-012 carry-forward, verification-only) |
| **Module boundary** | PASS | All work lives within HLD M-006 UI; integration is gated through `lib/api/*` wrappers (S2 pattern) |
| **API contract** | PASS | All 4 declared endpoints match LLD interfaces exactly (2 new from T-064/T-065, 2 existing from S1) |

## AC coverage detail

| AC | Components |
|---|---|
| AC-041..AC-044 (dashboard math + render) | DashboardView, DashboardTable |
| AC-045 (sub-second) | DashboardView — react-query with no client transform; trusts backend latency |
| AC-046 (filters optional, multi-select) | SalesReportFilterBar, MultiSelectCombobox |
| AC-047 (consolidation grouped + sorted) | ConsolidationTable (server-sorted, no client re-sort) |
| AC-048 (transactions sorted by sales_date) | TransactionsTable |
| AC-049 (both sections, no toggle, Consolidation first) | SalesReportView layout |
| AC-050 (reconciliation) | ReconciliationBadge — client-side defense-in-depth tick |
| AC-051..AC-053 (F-012) | **no UI surface** (carry-forward is observable via the existing DashboardTable) |

## Module boundary

All components live under `frontend/src/{app/admin/, components/, lib/, types/}` — exclusively within HLD M-006 (UI). Integration to other modules goes through:
- `lib/api/dashboard.ts` (new) → M-002 API → M-004 Dashboard
- `lib/api/reports.ts` (new) → M-002 API → M-005 Reports
- `lib/api/masters.ts` (existing S1) → M-002 API → M-001 Master (for dealer + design dropdowns)

**No boundary violations.** No component imports from `backend/`, from `lib/mocks.ts` directly, or from any module outside the integration boundary.

## API contract

| Spec endpoint | LLD reference | Match |
|---|---|---|
| `GET /api/v1/dashboard?as_of_date=YYYY-MM-DD` | `files[3]` + T-064 plan | ✓ exact |
| `GET /api/v1/reports/sales?date_from=&date_to=&dealer_ids=&places=&design_ids=` | `files[6]` + T-065 plan | ✓ exact |
| `GET /api/v1/designs` | S1 existing | ✓ existing wrapper |
| `GET /api/v1/dealers` | S1 existing | ✓ existing wrapper |

The spec's **explicit flag** about axios repeat-key serialization (`?dealer_ids=1&dealer_ids=2` NOT comma-joined) is correctly called out and matches FastAPI's native list parser. Scaffold must use `paramsSerializer` or `URLSearchParams`.

## Warnings (4, all minor, none blocking)

| ID | Topic | Resolution |
|---|---|---|
| **UR-S3-001** | Spec references backend type names `DealerRead`/`TradingDesignRead` while frontend uses `Dealer`/`Design` | Scaffold-time clarification — use existing frontend type names |
| **UR-S3-002** | Places multi-select derived from active dealers misses historical place_snapshot values that no longer match an active dealer | Carry-forward as V2 consideration; OK for V1 scale (single-digit users, small dealer set) |
| **UR-S3-003** | ASCII diagram shows reconciliation badge in two places but component is single — recommend ONE badge near the filter bar | Scaffold-time render choice |
| **UR-S3-004** | URL cleanup on Reset not explicit | Scaffold should drop empty params before `router.replace` |

## Strengths

- **Integration-boundary pattern** mirrors S2's `lib/api/transactions.ts` exactly — Sonnet's integration swap will be a 1-line change per function
- **Apply-button batching** in FilterBar avoids the per-keystroke refetch pitfall
- **URL sync** makes dashboards bookmarkable for deep-linked sharing
- **ReconciliationBadge** is high-trust UX — server already asserts AC-050, but the visible tick gives the PO concrete confirmation
- **TD-010 closure path** is concrete: MultiSelectCombobox spec includes a jsdom native-select shim
- **AC-049 layout** ("no tabs, no toggle, Consolidation first") encoded explicitly in SalesReportView interactions — eliminates ambiguity at scaffold time

## Decisions consulted

- **DS-010** (multi-device responsive) — honored with explicit mobile/tablet/desktop breakpoints
- **DS-013** (denormalized place snapshot) — honored; TransactionRow.place renders snapshot as-is
- **DS-016** (single-query dashboard aggregation) — honored; UI does not paginate or re-aggregate
- **DS-017** (shared filter predicate) — honored; UI sends one Apply for both queries

## No redesign needed

Per skill rule "Detection only — do not redesign". The 4 minor warnings are scaffold-time clarifications, not redesign requests. No structural changes required.

## Next
**`/ases-ui-scaffold S3`** — Gemini (or fallback in this session) builds the standalone Next.js scaffold against this spec. After scaffold: integration pass swaps `lib/api/{dashboard,reports}.ts` from mocks to real backend calls.
