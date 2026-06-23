# Sprint S2 — UI Specification (Transaction Forms)

**Produced by:** `/ases-ui-design` · **Date:** 2026-06-22 · **Sprint:** S2 (F-007 / F-008 / F-009)

## Scope
Three transaction-entry forms (Inward, Sales, Adjustment) plus their shared scaffolding (DatePicker, MasterSelect, hooks, api.ts, mocks.ts, types, zod schemas). 13 user-facing TCs (TC-090..TC-102).

## Routes
| Path | Page | Feature |
|---|---|---|
| `/inward/new` | InwardFormPage | F-007 |
| `/sales/new` | SalesFormPage | F-008 |
| `/adjustments/new` | AdjustmentFormPage | F-009 |

Navigation: new sidebar section **Transactions** with three entries, alongside S1's **Masters** section.

## Top-level component tree

```
InwardFormPage (server)
└── InwardForm (client)
    ├── DatePicker (shared)            ← purchase_date
    ├── MasterSelect[Supplier] (shared) → fires place read-only display
    ├── ReadOnlyField (shared)         ← place from supplier
    ├── MasterSelect[Staff] (shared)   ← entered_by
    ├── MasterSelect[Design] (shared)  ← drives line rows
    └── TransactionLineRow[] (shared)  ← one per active grade for selected design

SalesFormPage (server)
└── SalesForm (client)
    ├── DatePicker (shared)            ← sales_date
    ├── MasterSelect[Dealer]           → place read-only
    ├── ReadOnlyField                  ← place from dealer
    ├── MasterSelect[Staff] × 2        ← loading_staff_id + verified_by_id
    ├── MasterSelect[Design]
    └── TransactionLineRow[]

AdjustmentFormPage (server)
└── AdjustmentForm (client)
    ├── DatePicker × 2 (shared)        ← stock_date + entry_date
    ├── MasterSelect[Design] (shared)
    ├── MasterSelect[Staff] (shared)   ← entered_by
    ├── Err012Banner (when getGradesWithCb = []) ← AC-040
    └── AdjustmentLineRow[] (per response of getGradesWithCb)
        ├── grade_code (read)
        ├── software_cb (read, pre-filled)
        ├── physical_cb (number input)
        └── difference (live-computed read; aria-live=polite)
```

## Integration boundary

**The single file Sonnet may rewrite during integration:** `frontend/src/lib/api.ts`.
Components and hooks import ONLY from `api.ts`, never from `mocks.ts` directly.

```ts
// frontend/src/lib/api.ts (UI-time surface, returns mock data)
export const inwardApi = {
  create: async (payload: InwardCreate): Promise<InwardRead> => mockInwardCreateResponse(payload),
  list: async (filters?: {…}): Promise<InwardRead[]> => /* mock */,
};
export const salesApi = { create, list };  // mirror
export const adjustmentsApi = { create };  // POST only
// designsApi already exists from S1 — extend with:
designsApi.getGradesWithCb = async (designId: number, stockDate: string) => mockGetGradesWithCb[designId] ?? [];
```

Post-integration: `api.ts` body is rewritten to call axios against real backend. `mocks.ts` is deleted. **No other frontend file changes during integration.**

## Endpoints consumed

- POST `/api/v1/inward` (T-052)
- GET `/api/v1/inward` (T-052 — optional for verification)
- POST `/api/v1/sales` (T-053)
- GET `/api/v1/sales` (T-053 — optional)
- POST `/api/v1/adjustments` (T-054)
- GET `/api/v1/designs/{id}/grades-with-cb?stock_date=` (T-055)
- GET `/api/v1/designs/{id}/grades` (S1 — Inward+Sales auto-populate)
- GET `/api/v1/{suppliers,dealers,staff,designs}` (S1 lists)

## Validation (zod schemas)

### `inwardCreateSchema`
- `purchase_date`: `date()` + `.refine(d => d <= today, 'ERR-001')` + `.refine(d => d >= subDays(today, 7), 'ERR-002')`
- `supplier_id`, `entered_by_id`: `.int().positive()`
- `lines`: `.array(...).min(1)` + `.refine(arr => arr.some(l => l.nos != null && l.nos > 0), 'AC-026')`
  - Per row: `nos: z.number().int().nullable().refine(n => n === null || n >= 0, 'ERR-007')`

### `salesCreateSchema`
- Identical date refinements
- `dealer_id`, `loading_staff_id`, `verified_by_id`, `entered_by_id` (if applicable per backend): `.int().positive()`
- `lines`: same shape

### `adjustmentCreateSchema`
- `stock_date`, `entry_date`: `date()`
- `design_id`, `entered_by_id`: `.int().positive()`
- `lines`: `.array(z.object({ grade_id: z.number().positive(), physical_cb: z.number().int().nonnegative('ERR-009') })).min(1)`
- **Cross-field:** `.refine(d => d.stock_date <= d.entry_date, { message: 'ERR-010', path: ['entry_date'] })`

> Backend re-validates everything via Pydantic (T-046) + DB CHECK constraints (T-044). Client-side zod is UX-level only.

## Hooks (TanStack Query)

```ts
// frontend/src/hooks/transactions/

useGradesForDesign(designId?: number)
  // S1 endpoint; enabled: !!designId
  // returns { data: GradeReadMin[], isLoading, error }

useGradesWithCb(designId?: number, stockDate?: string)
  // T-055 endpoint; enabled: !!(designId && stockDate)
  // returns { data: DesignGradeReadWithCb[], isLoading, error }

useCreateInward()  // useMutation<InwardRead, ApiError, InwardCreate>
useCreateSale()    // useMutation<SalesRead, ApiError, SalesCreate>
useCreateAdjustment()  // useMutation<AdjustmentRead, ApiError, AdjustmentCreate>
```

Master hooks (`useSuppliers`, `useDealers`, `useStaff`, `useDesigns`) reused from S1.

## Mocks (`frontend/src/lib/mocks.ts`)

```ts
export const mockSuppliers: SupplierRead[] = [
  { supplier_id: 1, supplier_name: 'Manjunatha', place: 'Mallur', is_active: true, ... },
  { supplier_id: 2, supplier_name: 'Ramesh', place: 'Belgaum', is_active: true, ... },
  { supplier_id: 3, supplier_name: 'Inactive Co.', place: 'Hubli', is_active: false, ... },
];
export const mockDealers: DealerRead[] = [/* 3 */];
export const mockStaff: StaffRead[] = [/* 3 */];
export const mockDesigns: DesignRead[] = [/* 5; 3 active */];

export const mockGradesForDesign: Record<number, GradeReadMin[]> = {
  1: [{ grade_id: 1, grade_code: '1' }, { grade_id: 2, grade_code: 'OB' }],
  2: [/* … */],
  3: [], // for TC-102: design with no active grades
};

export const mockGetGradesWithCb: Record<number, DesignGradeReadWithCb[]> = {
  1: [
    { grade_id: 1, grade_code: '1', software_cb: 42 },
    { grade_id: 2, grade_code: 'OB', software_cb: 17 },
  ],
  3: [], // ERR-012 trigger for TC-102
};

export const throwApiError = (status: number, detail: string) => {
  const err = new Error(detail);
  (err as any).status = status;
  (err as any).detail = detail;
  throw err;
};
```

## Test coverage (TC-090..TC-102 → file mapping)

| TC | AC | Component | File |
|---|---|---|---|
| TC-090 | AC-020 | InwardForm | `inward/__tests__/InwardForm.test.tsx` |
| TC-091 | AC-021 | InwardForm | same |
| TC-092 | AC-022 | InwardForm | same |
| TC-093 | AC-023 | InwardForm | same |
| TC-094 | AC-024 | InwardForm | same |
| TC-095 | AC-026 | InwardForm | same |
| TC-096 | AC-028 | SalesForm | `sales/__tests__/SalesForm.test.tsx` |
| TC-097 | AC-030 | SalesForm | same |
| TC-098 | AC-035 | AdjustmentForm | `adjustment/__tests__/AdjustmentForm.test.tsx` |
| TC-099 | AC-036 | AdjustmentForm | same |
| TC-100 | AC-037 | AdjustmentForm | same |
| TC-101 | AC-038 | AdjustmentForm | same |
| TC-102 | AC-040 | AdjustmentForm | same |

Test stack: `jest@29 + @testing-library/react + userEvent`. `api.ts` mocked per test via `jest.mock('@/lib/api', () => …)`.

## Responsive

- **Mobile (< 640px):** single-column form; line rows collapse into stacked cards. Sticky submit bar at bottom.
- **Tablet (640-1024px):** 2-column header; line rows as horizontal table.
- **Desktop (> 1024px):** 2-column header expanded; line table 4 columns wide; submit right-aligned.

Tailwind responsive utility classes drive the breakpoints; no JS-level conditional rendering.

## Accessibility

| Concern | Treatment |
|---|---|
| Label↔Input | shadcn primitives wire `htmlFor`/`id` automatically; preserve |
| Validation errors | `<p role="alert" id="<field>-error">…</p>` adjacent to input; `aria-describedby` points to it |
| Required fields | `aria-required="true"` |
| DatePicker | shadcn calendar already implements keyboard nav + `aria-label`; preserve |
| Submit busy | `aria-busy={mutation.isPending}` |
| ERR-012 banner | `role="alert"` so SRs announce on appearance (TC-102) |
| Live difference | `aria-live="polite"` so SRs announce changes (TC-101) without interrupting typing |
| Color | Validation errors paired with icon + text — color is NOT the only indicator |

## UI sub-tasks for `/ases-ui-scaffold`

| ID | Name | TC refs |
|---|---|---|
| UI-T-001 | InwardFormPage + InwardForm + line rows + hooks/mutation | TC-090..095 |
| UI-T-002 | SalesFormPage + SalesForm + 4-filter list_sales backbone | TC-096, 097 |
| UI-T-003 | AdjustmentFormPage + AdjustmentForm + AdjustmentLineRow + Err012Banner | TC-098..102 |
| UI-T-004 | Shared: DatePicker, MasterSelect, api.ts, mocks.ts, types/transactions.ts, schemas.ts, 5 hooks | — |
| UI-T-005 | Nav sidebar — add Transactions section + 3 links (modify S1 file) | — |

## Out of scope (S2)

- Admin list pages for /inward and /sales (LLD endpoints exist; S3 Sales Report consumes them)
- Edit/delete transaction flows — V1 treats transactions as immutable; Adjustment is the correction mechanism
- Pagination on master lists
- Export to PDF/CSV (deferred to V2)

## Open questions

None. Ready for review.

→ Next: `/ases-ui-review S2`
