# Sprint S2 — UI Scaffold Manifest

**Produced:** 2026-06-23 · **Lock status:** 🔒 **LOCKED**

The transaction UI scaffold is complete. Per ASES rule 6, Sonnet may only edit function bodies in declared `integration_points[].file` (currently `frontend/src/lib/api/transactions.ts`). Any structural change requires a new `ui-design → ui-review → ui-scaffold` cycle.

## Files created (16)

| Layer | File |
|---|---|
| Types | `frontend/src/types/transactions.ts` |
| Schemas | `frontend/src/lib/validation/transaction-schemas.ts` |
| API boundary (S2) | `frontend/src/lib/api/transactions.ts` |
| Shared UI | `frontend/src/components/ui/date-picker.tsx` |
| Shared TX | `frontend/src/components/transactions/shared/TransactionLineRow.tsx` |
| F-007 | `frontend/src/components/transactions/inward/InwardForm.tsx` |
| F-008 | `frontend/src/components/transactions/sales/SalesForm.tsx` |
| F-009 | `frontend/src/components/transactions/adjustment/AdjustmentForm.tsx` |
| F-009 | `frontend/src/components/transactions/adjustment/AdjustmentLineRow.tsx` |
| F-009 | `frontend/src/components/transactions/adjustment/Err012Banner.tsx` |
| Page | `frontend/src/app/admin/inward/new/page.tsx` |
| Page | `frontend/src/app/admin/sales/new/page.tsx` |
| Page | `frontend/src/app/admin/adjustments/new/page.tsx` |
| Test | `frontend/src/components/transactions/inward/__tests__/InwardForm.test.tsx` |
| Test | `frontend/src/components/transactions/sales/__tests__/SalesForm.test.tsx` |
| Test | `frontend/src/components/transactions/adjustment/__tests__/AdjustmentForm.test.tsx` |

## Files modified (2)

| File | Change |
|---|---|
| `frontend/src/lib/mocks.ts` | Appended `MOCK_INWARDS`, `MOCK_SALES`, `MOCK_ADJUSTMENTS`, `MOCK_RUNNING_BALANCE` + helpers `bumpBalance / getBalance / projectGradesWithCb`. S1 contents untouched. |
| `frontend/src/app/admin/layout.tsx` | Refactored `NAV` array into `NAV_GROUPS` with two groups (Masters / Transactions); added 3 nav items + 3 lucide icon imports (PackagePlus, ShoppingCart, Scale). Existing 6 master links preserved. |

## Integration points (6)

The 6 functions in `frontend/src/lib/api/transactions.ts` are the only files Sonnet rewrites at integration time:

| ID | Export | Real endpoint | Backend owner |
|---|---|---|---|
| IP-S2-001 | `inwardApi.create` | POST /api/v1/inward | T-052 + T-047 |
| IP-S2-002 | `inwardApi.list` | GET /api/v1/inward | T-052 + T-047 |
| IP-S2-003 | `salesApi.create` | POST /api/v1/sales | T-053 + T-048 |
| IP-S2-004 | `salesApi.list` | GET /api/v1/sales | T-053 + T-048 |
| IP-S2-005 | `adjustmentsApi.create` | POST /api/v1/adjustments | T-054 + T-049 |
| IP-S2-006 | `designsTxApi.getGradesWithCb` | GET /api/v1/designs/{id}/grades-with-cb | T-055 + T-050 |

Each has a `real_impl_hint` in the JSON manifest showing the exact axios call to swap in.

## Routes (3)

| Path | Page |
|---|---|
| `/admin/inward/new` | InwardForm |
| `/admin/sales/new` | SalesForm |
| `/admin/adjustments/new` | AdjustmentForm |

**Deviation from spec (SC-S2-001):** spec said `/inward/new` etc. at top level; relocated under `/admin/*` to reuse S1's `AdminLayout` sidebar. Nav grouping handles the user-facing separation between Masters and Transactions. Reversible by folder rename.

## Design choices captured

- **SC-S2-001** — Routes under `/admin/*` (above)
- **SC-S2-002** — `designsTxApi` lives in `api/transactions.ts` (not extending S1's `designsApi`) — keeps S1 untouched
- **SC-S2-003** — UR-W008 fix: `useEffect(.., [queryData, replace])` reactively syncs field-array on refetch (all 3 forms)
- **SC-S2-004** — UR-W007 fix: canonical naming; no parallel `GradeReadMin` alias; Inward/Sales reuse S1's `DesignGradeMin`
- **SC-S2-005** — Zero-difference adjustment lines still sent to server; T-049 skips ledger write but persists audit row
- **SC-S2-006** — zod (client) + Pydantic (server) + DB CHECK defense-in-depth

## Review warnings resolved

- **UR-W007 (minor)** — ✅ RESOLVED: canonical names used, no parallel alias
- **UR-W008 (advisory)** — ✅ RESOLVED: `useEffect` reactive sync applied to all 3 forms

## Test coverage

| TC | Form | Status |
|---|---|---|
| TC-092 | InwardForm — supplier→place snapshot | ✅ implemented |
| TC-093 | InwardForm — design→grade rows | ✅ implemented |
| TC-095 | InwardForm — all-blank-nos blocks save | ✅ implemented |
| TC-097 | SalesForm — verified_by_id required | ✅ implemented |
| TC-099 | AdjustmentForm — software_cb pre-fill | ✅ implemented |
| TC-101 | AdjustmentForm — live difference | ✅ implemented |
| TC-102 | AdjustmentForm — Err012Banner + disabled submit | ✅ implemented |
| TC-090, TC-091, TC-094, TC-096, TC-098, TC-100 | zod-validator-only edge cases | 🟡 deferred to /ases-test-impl S2 |

7 of 13 TCs implemented at scaffold time; 6 zod-only cases deferred to `/ases-test-impl S2` where the test infrastructure pattern will batch-produce them efficiently.

## Responsive + a11y

- **Mobile (default)**: single-column header grid, compact 2-col line rows
- **Tablet (`sm:`)**: 2-col header grid, multi-col line rows with extras
- **Desktop (`lg:`)**: same as tablet within admin layout's `max-w-6xl`

A11y: shadcn primitives wire `htmlFor`/`id`; validation errors use `role="alert"` + `aria-describedby`; required Selects use `aria-required="true"`; submit uses `aria-busy`; ERR-012 banner is `role="alert"`; live difference wraps in `aria-live="polite"`.

## Verification

```bash
cd frontend
npx tsc --noEmit                     # type-check
npm run lint                         # ESLint
npm test -- --testPathPattern='transactions'  # 3 test files
npm run dev                          # http://localhost:3000/admin/inward/new
```

## Lock policy

🔒 **The frontend scaffold is LOCKED after this step.** Sonnet may ONLY touch:
- Function bodies in `frontend/src/lib/api/transactions.ts` (the 6 IP-S2-* integration points)
- May delete `frontend/src/lib/mocks.ts` once all 6 IPs are swapped to real `apiClient.*` calls (and ensure no other code paths still reference mocks)

Any structural change (new component, new route, layout change) requires a new `ui-design → ui-review → ui-scaffold` cycle.

→ Next: `/ases-sprint-close S2`
