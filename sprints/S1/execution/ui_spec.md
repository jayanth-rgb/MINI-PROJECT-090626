# UI Design Specification — Sprint S1

**Produced by:** `/ases-ui-design S1`
**Tasks covered:** T-026 through T-040 (15 UI tasks)
**Companion JSON:** [ui_spec.json](./ui_spec.json)
**Inputs:** [lld.json](../design/lld.json), [tasks.json](./tasks.json), [schema.json](../design/schema.json), [test_cases.json](../design/test_cases.json)

---

## 1. Design Overview

S1 frontend delivers a **master data administration panel** — 6 CRUD admin screens (Suppliers, Staff, Dealers, Grades, Designs, Design-Grade Map) sharing a sidebar navigation shell and common table + dialog patterns.

### Architecture pattern

```
app/layout.tsx (QueryProvider + Toaster)
└── app/admin/layout.tsx (Sidebar + Main panel)
    ├── app/admin/suppliers/page.tsx → SupplierForm
    ├── app/admin/staff/page.tsx → StaffForm
    ├── app/admin/dealers/page.tsx → DealerForm
    ├── app/admin/grades/page.tsx → GradeForm
    ├── app/admin/designs/page.tsx → DesignForm
    └── app/admin/design-grade-map/page.tsx → DesignGradeMapForm
```

All pages are `'use client'` components using:
- **TanStack Query** for data fetching and cache invalidation
- **react-hook-form + Zod** for form state and validation (DS-011)
- **shadcn/ui** primitives (Table, Dialog, Button, Input, Label, Select, Badge)
- **sonner** for toast notifications

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.1.3 |
| React | React 19 | 19.0.0 |
| UI Components | shadcn/ui (radix-nova) | 4.x |
| CSS | TailwindCSS | 3.4 |
| Forms | react-hook-form + @hookform/resolvers/zod | 7.54 + 3.9 |
| Validation | Zod | 3.24 |
| Data fetching | @tanstack/react-query | 5.62 |
| HTTP client | axios | 1.7 |
| Icons | lucide-react | latest |
| Toast | sonner | 2.x |
| Font | Inter (next/font/google) | 400–700 |

---

## 3. Design System

### Color palette (oklch CSS variables)

Colors are inherited from the existing shadcn `globals.css` — neutral palette with dark mode support.

| Token | Light | Dark |
|-------|-------|------|
| `--background` | oklch(1 0 0) white | oklch(0.145 0 0) near-black |
| `--primary` | oklch(0.205 0 0) dark | oklch(0.922 0 0) light |
| `--destructive` | oklch(0.577 0.245 27) red | oklch(0.704 0.191 22) softer red |
| `--muted` | oklch(0.97 0 0) off-white | oklch(0.269 0 0) dark gray |
| `--sidebar` | oklch(0.985 0 0) light gray | oklch(0.205 0 0) dark |

### Typography

- **Font:** Inter via `next/font/google` (weights: 400, 500, 600, 700)
- **Page title:** `text-3xl font-bold tracking-tight`
- **Section heading:** `text-xl font-semibold`
- **Body / table cells:** `text-sm`
- **Labels:** `text-sm font-medium`
- **Error text:** `text-sm text-destructive`

### Spacing & layout

- **Border radius:** `0.625rem` (var(--radius))
- **Page padding:** `p-6 lg:p-8`
- **Form field gap:** `space-y-4`
- **Sidebar width:** `w-64` (16rem)
- **Content max-width:** `max-w-6xl`

---

## 4. Layout Structure

### 4.1 Root Layout (T-031)

**File:** `frontend/src/app/layout.tsx`

```
<html lang="en">
  <body className={inter.className}>
    <QueryProvider>
      {children}
      <Toaster richColors closeButton position="top-right" />
    </QueryProvider>
  </body>
</html>
```

- Server component (no `'use client'`)
- Loads Inter font via `next/font/google`
- Exports metadata: `{ title: 'Jayanth Trading Tiles', description: '...' }`

### 4.2 Home Page (T-031)

**File:** `frontend/src/app/page.tsx`

Server component that calls `redirect('/admin/suppliers')` — S1 has no dashboard.

### 4.3 Admin Layout (T-032)

**File:** `frontend/src/app/admin/layout.tsx`

```
┌──────────────────┬─────────────────────────────────────┐
│                  │                                     │
│   SIDEBAR        │         MAIN CONTENT                │
│   w-64, fixed    │         ml-64, flex-1               │
│                  │                                     │
│   ┌────────────┐ │   ┌─────────────────────────────┐   │
│   │ Logo       │ │   │  Page title   [+ Add Btn]   │   │
│   │ Jayanth    │ │   ├─────────────────────────────┤   │
│   │ Trading    │ │   │                             │   │
│   ├────────────┤ │   │        DATA TABLE           │   │
│   │ Suppliers  │ │   │                             │   │
│   │ Staff      │ │   │                             │   │
│   │ Dealers    │ │   │                             │   │
│   │ Grades     │ │   └─────────────────────────────┘   │
│   │ Designs    │ │                                     │
│   │ DG Map     │ │                                     │
│   └────────────┘ │                                     │
│                  │                                     │
└──────────────────┴─────────────────────────────────────┘
```

**Sidebar:**
- Fixed-position, full-height, `w-64`
- Border-right separator, `bg-sidebar text-sidebar-foreground`
- Header: Logo icon (Layers from lucide) + "Jayanth Trading" + "Tiles Management" subtitle
- Navigation links with icons:

| Label | Route | Icon |
|-------|-------|------|
| Suppliers | `/admin/suppliers` | `Truck` |
| Staff | `/admin/staff` | `Users` |
| Dealers | `/admin/dealers` | `Store` |
| Grades | `/admin/grades` | `Tags` |
| Designs | `/admin/designs` | `Palette` |
| Design-Grade Map | `/admin/design-grade-map` | `GitBranch` |

- Active link: `bg-sidebar-accent text-sidebar-accent-foreground font-medium`
- Inactive link: `text-muted-foreground hover:bg-sidebar-accent/50`
- Link style: `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200`
- Uses `usePathname()` for active state detection

**Main content:** `ml-64 flex-1 min-h-screen bg-background` with inner `p-6 lg:p-8 max-w-6xl`

---

## 5. Shared Components

### 5.1 MasterDataTable (T-033)

**File:** `frontend/src/components/admin/MasterDataTable.tsx`
**Type:** `MasterDataTable<T extends Record<string, unknown>>`

Generic data table used by all 6 admin pages.

| Prop | Type | Description |
|------|------|-------------|
| `rows` | `T[]` | Data array |
| `columns` | `{ key: keyof T; label: string }[]` | Column config |
| `rowKey` | `(row: T) => string \| number` | Unique key |
| `isActive` | `(row: T) => boolean` | Active status |
| `onEdit` | `(row: T) => void` | Edit handler |
| `onToggleActive` | `(row: T) => void` | Toggle handler |
| `isLoading?` | `boolean` | Shows skeleton |

**Visual spec:**
- Header: `bg-muted/50 text-muted-foreground text-xs uppercase tracking-wider font-medium`
- Active rows: `border-b hover:bg-muted/30 transition-colors`
- Inactive rows: `border-b opacity-50 bg-muted/10`
- Status column: Badge component — Active (emerald) / Inactive (muted)
- Actions column (right-aligned):
  - **Edit:** ghost button with `Pencil` icon
  - **Deactivate:** ghost button with `EyeOff` icon, destructive text
  - **Reactivate:** ghost button with `Eye` icon, emerald text
- Empty state: `"No records found."` centered in `p-8 text-muted-foreground`
- Loading state: 5 `Skeleton` rows

**Test IDs:** `master-data-table`, `edit-btn-{id}`, `toggle-btn-{id}`

### 5.2 MasterFormDialog (T-034)

**File:** `frontend/src/components/admin/MasterFormDialog.tsx`

Reusable modal wrapper for create/edit forms.

| Prop | Type | Description |
|------|------|-------------|
| `open` | `boolean` | Dialog visibility |
| `onOpenChange` | `(open: boolean) => void` | Toggle callback |
| `title` | `string` | "Add Supplier" / "Edit Supplier" |
| `children` | `ReactNode` | Form body |
| `formId` | `string` | Links Save to form submit |
| `isSubmitting` | `boolean` | Disables Save + shows spinner |

**Visual spec:**
- Overlay: `bg-black/40 backdrop-blur-sm`
- Panel: `sm:max-w-[480px] rounded-xl border shadow-lg`
- Header: `DialogTitle text-lg font-semibold`
- Body: `px-6 py-4`
- Footer: `flex justify-end gap-3 px-6 py-4 border-t bg-muted/30`
  - Cancel: `variant='outline'`
  - Save: `variant='default' type='submit' form={formId}`; shows `Loader2` spinner when `isSubmitting`
- Accessibility: `DialogDescription` with `sr-only` class

**Test IDs:** `master-form-dialog`, `dialog-save-btn`, `dialog-cancel-btn`

---

## 6. Per-Entity Admin Pages

All 6 pages follow the same structural pattern:

### 6.1 Common page pattern

**Header:**
```
┌──────────────────────────────────────────┐
│  <h1>Entity Name</h1>    [+ Add Entity] │
└──────────────────────────────────────────┘
```
- `flex items-center justify-between mb-6`
- Title: `text-3xl font-bold tracking-tight`
- Add button: `variant='default'` with `Plus` icon

**State management (per page):**
```typescript
// Query
const { data, isLoading } = useQuery({
  queryKey: ['{entity}'],
  queryFn: {entity}Api.list,
});

// Mutations
const createMutation = useMutation({
  mutationFn: {entity}Api.create,
  onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['{entity}'] }); toast.success('Created'); dialog.close(); },
  onError: (err) => toast.error(err.response?.data?.message || 'Error'),
});

// Dialog state
const [dialogState, setDialogState] = useState<{ mode: 'create' | 'edit'; data?: T } | null>(null);
```

**Toast behavior:**
| Event | Toast |
|-------|-------|
| Create success | `toast.success('{Entity} created successfully')` |
| Update success | `toast.success('{Entity} updated successfully')` |
| Deactivate success | `toast.success('{Entity} deactivated')` |
| Reactivate success | `toast.success('{Entity} reactivated')` |
| 409 conflict | `toast.error(server message)` |
| Generic error | `toast.error('An error occurred')` |

### 6.2 Common form pattern

```typescript
const { register, handleSubmit, formState: { errors } } = useForm<TCreate>({
  resolver: zodResolver(tSchema),
  defaultValues,
});

return (
  <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-4">
    <div>
      <Label htmlFor="fieldName">Field Label</Label>
      <Input id="fieldName" placeholder="..." {...register('fieldName')} />
      {errors.fieldName && <p className="text-sm text-destructive mt-1">{errors.fieldName.message}</p>}
    </div>
  </form>
);
```

### 6.3 Entity-specific details

#### Suppliers (T-035)

| | |
|---|---|
| Route | `/admin/suppliers` |
| AC | AC-001 (create name+place required), AC-002 (soft delete) |
| Columns | ID · Name · Place · Status |
| Form fields | `supplier_name` (Input, required) · `place` (Input, required) |
| Zod | `supplierSchema` |

#### Staff (T-036)

| | |
|---|---|
| Route | `/admin/staff` |
| AC | AC-004 (staff_name required), AC-005 (soft delete) |
| Columns | ID · Name · Status |
| Form fields | `staff_name` (Input, required) |
| Zod | `staffSchema` |

#### Dealers (T-037)

| | |
|---|---|
| Route | `/admin/dealers` |
| AC | AC-007 (name+place required), AC-008 (soft delete) |
| Columns | ID · Name · Place · Status |
| Form fields | `dealer_name` (Input, required) · `place` (Input, required) |
| Zod | `dealerSchema` |

#### Grades (T-038)

| | |
|---|---|
| Route | `/admin/grades` |
| AC | AC-011 (UNIQUE grade_code), AC-012 (deactivate) |
| Columns | ID · Grade Code · Status |
| Form fields | `grade_code` (Input, required) |
| Zod | `gradeSchema` |
| **Special** | API returns 409 on duplicate → `toast.error('Grade code already exists')` |

#### Trading Designs (T-039)

| | |
|---|---|
| Route | `/admin/designs` |
| AC | AC-013 (size+name required), AC-015 (soft delete) |
| Columns | ID · Size · Design Name · Status |
| Form fields | `size` (Input, required) · `design_name` (Input, required) |
| Zod | `designSchema` |

#### Design-Grade Map (T-040)

| | |
|---|---|
| Route | `/admin/design-grade-map` |
| AC | AC-016 (UNIQUE pair), AC-017 (deactivate) |
| Columns | ID · Design · Grade · Status |
| Form fields | `design_id` (Select, required) · `grade_id` (Select, required) |
| Zod | `designGradeMapSchema` |
| **Special** | Two Select dropdowns populated from `designsApi.list` and `gradesApi.list` (active only). API returns 409 on duplicate pair → `toast.error('This design-grade combination already exists')`. Select uses `Controller` from react-hook-form with `onValueChange` converting string→number via `parseInt`. |

---

## 7. Plumbing Components

### 7.1 TypeScript Types (T-026)

**File:** `frontend/src/types/masters.ts`

19 types mirroring backend Pydantic schemas:
- 6 Read types (Supplier, Staff, Dealer, Grade, Design, DesignGradeMap)
- 6 Create types (SupplierCreate, StaffCreate, etc.)
- 6 Update types (SupplierUpdate, StaffUpdate, etc.)
- 1 minimal projection (DesignGradeMin — for GET /designs/{id}/grades)

### 7.2 API Client (T-027)

**File:** `frontend/src/lib/api/client.ts`

Axios instance with:
- `baseURL: process.env.NEXT_PUBLIC_API_URL`
- Default `Content-Type: application/json`
- Response error interceptor: catches errors, throws `{ status, message }` for consistent handling

### 7.3 API Wrappers (T-028)

**File:** `frontend/src/lib/api/masters.ts`

6 API namespaces (one per entity), each with `{ list, create, update, remove }`:
- `suppliersApi` → `/suppliers`
- `staffApi` → `/staff`
- `dealersApi` → `/dealers`
- `gradesApi` → `/grades`
- `designsApi` → `/designs` + `getGrades(designId)` (DF-006 contract)
- `designGradeMapApi` → `/design-grade-map`

### 7.4 QueryProvider (T-029)

**File:** `frontend/src/lib/query/provider.tsx`

`'use client'` component wrapping children with `QueryClientProvider`:
- `staleTime: 30_000` (30 seconds)
- `refetchOnWindowFocus: false`
- `retry: 1`

### 7.5 Zod Schemas (T-030)

**File:** `frontend/src/lib/validation/master-schemas.ts`

6 Zod schemas with user-friendly error messages:
- `supplierSchema`: name + place required (min 1 char)
- `staffSchema`: name required
- `dealerSchema`: name + place required
- `gradeSchema`: grade_code required
- `designSchema`: size + design_name required
- `designGradeMapSchema`: design_id + grade_id (positive integers)

---

## 8. Interaction Flows

### 8.1 Create

```
[Click Add] → Dialog opens (empty form)
→ Fill fields → Submit
→ Zod validation fail? → Inline errors below fields, dialog stays open
→ Zod validation pass → Save button disabled + spinner
→ API success → Dialog closes, list refreshes, success toast
→ API 409 → Dialog stays open, error toast with server message
→ API error → Dialog stays open, generic error toast
```

### 8.2 Edit

```
[Click Edit pencil on row] → Dialog opens (pre-filled form)
→ Same flow as Create
→ API sends PATCH with changed fields only
```

### 8.3 Deactivate / Reactivate

```
[Click EyeOff on active row] → DELETE /entity/{id} (soft delete)
→ Row becomes muted in table, success toast

[Click Eye on inactive row] → PATCH /entity/{id} { is_active: true }
→ Row becomes active, success toast
```

---

## 9. Status Rendering

| Status | Badge | Style |
|--------|-------|-------|
| Active | `<Badge>Active</Badge>` | `bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400` |
| Inactive | `<Badge variant="secondary">Inactive</Badge>` | Default muted styling |

---

## 10. Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| `< md` | Sidebar hidden; hamburger menu in top-left opens Sheet overlay |
| `md+` | Fixed sidebar, main content offset |
| Table | `overflow-x-auto` wrapper for horizontal scroll |
| Dialog | Full-width on mobile, `sm:max-w-[480px]` on desktop |
| Padding | `p-4` mobile, `p-6 lg:p-8` desktop |

---

## 11. Error Handling

| Scenario | UI Response |
|----------|-------------|
| Query fetch fails | Red alert box with `RefreshCw` icon + "Retry" button |
| Form validation fails | Inline error `<p>` below each invalid field |
| API 409 (conflict) | `toast.error` with server message |
| API 404 | `toast.error('Record not found')` |
| API 422 | `toast.error` with validation details |
| API 500 | `toast.error('Unexpected error')` |

---

## 12. Keyboard Accessibility

- All interactive elements reachable via **Tab**
- Dialog focus-trapped when open (shadcn default)
- **Enter** submits form when input or Save focused
- **Escape** closes dialog (shadcn default)
- Required-field highlighting on submit error (red border + error text)

---

## 13. Integration Points

| Point | Detail |
|-------|--------|
| S2 contract | `designsApi.getGrades(designId)` → `GET /designs/{id}/grades` delivered in T-028 |
| Forms | All 6 use react-hook-form + Zod (DS-011, closes TD-002) |
| Data fetching | All pages use TanStack Query |
| Cache invalidation | All mutations invalidate their entity's query key |

---

## 14. Test IDs

Every interactive element has a unique `data-testid` for TC-039 through TC-046:

| Element | Pattern |
|---------|---------|
| Page container | `{entity}-page` |
| Add button | `add-{entity}-btn` |
| Table | `master-data-table` |
| Edit button | `edit-btn-{id}` |
| Toggle button | `toggle-btn-{id}` |
| Dialog | `master-form-dialog` |
| Save button | `dialog-save-btn` |
| Cancel button | `dialog-cancel-btn` |
| Form inputs | `{entity}-{field}-input` |
| Select triggers | `{entity}-select` |

---

## 15. Mock Strategy & Integration Boundary

**Hard rule:** components, hooks, and pages ONLY import from the integration boundary — never from mocks directly.

| Slot | Path | Lock state |
|------|------|-----------|
| Integration boundary | `frontend/src/lib/api/masters.ts` | The ONLY file Sonnet may rewrite during backend-integration pass |
| Mock data module | `frontend/src/lib/mocks.ts` | Created by `/ases-ui-scaffold`; deleted after backend integration |
| All other frontend files | `frontend/src/{types,components,app,lib/query,lib/validation,lib/api/client.ts}/**` | Locked after `/ases-ui-scaffold` |

### Scaffold phase (`/ases-ui-scaffold S1`)

`frontend/src/lib/mocks.ts` exports deterministic in-memory data matching the PRD seeds (3 suppliers, 9 staff, 3 dealers, 9 grades, 3 designs, 6 design-grade mappings). During scaffold, `masters.ts` implements `suppliersApi.list/create/update/remove` etc. against these arrays so the Next.js app is fully usable without a backend.

`designGradeMapApi.create` throws a synthetic `{ status: 409, message: '(design_id, grade_id) already exists' }` on a duplicate pair so TC-045's toast flow is reproducible offline. Same pattern for `gradesApi.create` and TC-043 (duplicate grade_code).

### Integration phase

When the backend track lands `/ases-validate T-027`, Sonnet rewrites `frontend/src/lib/api/masters.ts` ONLY — swapping in-memory operations for `apiClient.get/post/patch/delete` calls. `mocks.ts` is then deleted. Verification:

```bash
grep -r "from .*mocks" frontend/src   # must be empty
npm run typecheck                      # passes
npm test                               # TC-039..TC-046 still pass
```

---

## 16. Next Step

→ **`/ases-ui-review S1`** — Review the UI spec for completeness, consistency with LLD, and design quality. Then → `/ases-ui-scaffold S1`.
