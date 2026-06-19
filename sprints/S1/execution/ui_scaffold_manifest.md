# Sprint S1 — UI Scaffold Manifest

**Produced by:** `/ases-ui-scaffold S1`
**Companion JSON:** [ui_scaffold_manifest.json](./ui_scaffold_manifest.json)
**Companion spec:** [ui_spec.json](./ui_spec.json) · [ui_review.json](./ui_review.json)

---

## Build verification

| Check | Result |
|-------|--------|
| `npm run typecheck` | **PASS** — tsc --noEmit clean |
| `npm run build` | **PASS** — 8 static routes generated |
| Routes built | `/`, `/admin/suppliers`, `/admin/staff`, `/admin/dealers`, `/admin/grades`, `/admin/designs`, `/admin/design-grade-map`, `/_not-found` |
| Bundle first-load | 105 kB shared, 173 kB per admin page |

Verified 2026-06-16.

---

## Files created (23 source + manifest)

### Types
- [frontend/src/types/masters.ts](../../../frontend/src/types/masters.ts) — Supplier/Staff/Dealer/Grade/Design/DesignGradeMap Read/Create/Update + ApiError

### Library
- [frontend/src/lib/mocks.ts](../../../frontend/src/lib/mocks.ts) — in-memory PRD-seed data; **deleted after integration**
- [frontend/src/lib/api/client.ts](../../../frontend/src/lib/api/client.ts) — axios + error interceptor (W-001 fix: `detail` first)
- [frontend/src/lib/api/masters.ts](../../../frontend/src/lib/api/masters.ts) — **🔓 INTEGRATION BOUNDARY** (the only file Sonnet rewrites)
- [frontend/src/lib/query/provider.tsx](../../../frontend/src/lib/query/provider.tsx) — TanStack Query provider
- [frontend/src/lib/validation/master-schemas.ts](../../../frontend/src/lib/validation/master-schemas.ts) — Zod schemas

### App Router
- [frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx) — root with Inter font, QueryProvider, Toaster
- [frontend/src/app/page.tsx](../../../frontend/src/app/page.tsx) — redirect to /admin/suppliers
- [frontend/src/app/admin/layout.tsx](../../../frontend/src/app/admin/layout.tsx) — sidebar + mobile drawer
- `app/admin/{suppliers,staff,dealers,grades,designs,design-grade-map}/page.tsx` — 6 master pages

### Components
- [MasterDataTable.tsx](../../../frontend/src/components/admin/MasterDataTable.tsx) — generic table, per-column `render` (W-005 fix)
- [MasterFormDialog.tsx](../../../frontend/src/components/admin/MasterFormDialog.tsx) — Dialog wrapper
- `components/admin/{entity}/{Entity}Form.tsx` — 6 forms

### Sprint-scaffold fixes (infrastructure, not UI structure)

| File | Fix |
|------|-----|
| `frontend/tailwind.config.js` | Extended theme with shadcn CSS-variable tokens + tailwindcss-animate plugin. Sprint-scaffold left an empty `extend{}`. |
| `frontend/src/app/globals.css` | Replaced Tailwind v4 imports (`@import "tw-animate-css"`, `@import "shadcn/tailwind.css"`) with v3 directives (`@tailwind base/components/utilities`). Project is on tailwindcss 3.4. |
| `frontend/jest.config.ts` | Renamed `setupFilesAfterEach` → `setupFilesAfterEnv` — typo that blocked `tsc`. |

---

## 🔒 Lock policy

All files under `frontend/src/**` are **LOCKED** after this step **EXCEPT**:

- **`frontend/src/lib/api/masters.ts`** — Sonnet may rewrite this file ONLY during `/ases-dev` to swap mock implementations for live `apiClient` calls.
- **`frontend/src/lib/mocks.ts`** — Sonnet **deletes** this file once all `masters.ts` functions point at the real backend.

Any structural change (new component, new route, layout edit) requires a new `ui-design → ui-review → ui-scaffold` cycle.

---

## Integration boundary — `lib/api/masters.ts`

Six exported namespaces. Each method's live endpoint is documented in the JSON manifest. During scaffold all methods proxy to `@/lib/mocks` helpers; integration phase replaces bodies with `apiClient.get/post/patch/delete` calls.

| Namespace | Live endpoint base | Special behaviour |
|-----------|--------------------|-------------------|
| `suppliersApi` | `/api/v1/suppliers` | DELETE returns deactivated row (DS-008) |
| `staffApi` | `/api/v1/staff` | DELETE returns deactivated row |
| `dealersApi` | `/api/v1/dealers` | DELETE returns deactivated row |
| `gradesApi` | `/api/v1/grades` | POST 409 on duplicate grade_code (AC-011) |
| `designsApi` | `/api/v1/designs` | + `getGrades(id)` → `/designs/{id}/grades` (DF-006, AC-019) |
| `designGradeMapApi` | `/api/v1/design-grade-map` | POST 409 on duplicate pair (AC-016), 404 on bad FK |

### Error contract

```ts
interface ApiError { status: number; detail: string }
```

Mocks throw `{ status, detail }` directly. The live interceptor reads `response.data.detail` (FastAPI HTTPException convention) and rejects with the same shape. Page-level `useMutation.onError` handlers always do `toast.error(e.detail)`.

---

## ui-review warnings — disposition

| ID | Status | Notes |
|----|--------|-------|
| **UR-W001** | ✅ RESOLVED | `client.ts` interceptor prefers `data.detail` first |
| **UR-W002** | ⏭ DEFERRED to `/ases-dev T-007` | Pydantic `*Update` schemas should declare `is_active: bool \| None` |
| **UR-W004** | ✅ RESOLVED | `mocks.ts` throws `{status, detail}` matching live shape |
| **UR-W005** | ✅ RESOLVED | `MasterDataTable` accepts per-column `render`; every page passes `statusBadge(row.is_active)` |

---

## Responsive implementation (DS-010)

| Breakpoint | Behaviour |
|-----------|-----------|
| `md+` (≥768px) | Fixed 64-wide sidebar, main content `ml-64` with `max-w-6xl` |
| `<md` mobile | Hamburger menu in `h-14` top bar opens slide-in drawer (left); nav items auto-collapse drawer on tap |
| Table | Wrapped in `overflow-x-auto` — columns scroll horizontally on narrow viewports |
| Dialog | `sm:max-w-[480px]` — full-width on phone |

Tablet = desktop layout from `md` up. ui_spec did not specify a distinct tablet view; matches the spec's three-breakpoint definition.

---

## Feature → AC coverage

| Feature | Page | ACs covered |
|---------|------|------------|
| F-001 Suppliers | `/admin/suppliers` | AC-001, AC-002 |
| F-002 Staff | `/admin/staff` | AC-004, AC-005 |
| F-003 Dealers | `/admin/dealers` | AC-007, AC-008 |
| F-004 Grades | `/admin/grades` | AC-011 (409 toast), AC-012 |
| F-005 Designs | `/admin/designs` | AC-013, AC-015 |
| F-006 Design-Grade Map | `/admin/design-grade-map` | AC-016 (409 toast), AC-017, + AC-019 (DF-006 contract surface) |

---

## Next step

→ **`/ases-validate T-001 S1`** — Begin backend execution loop. The 6 admin pages are visible end-to-end via `npm run dev` against the mock data immediately; the backend integration pass happens later via `/ases-dev T-028` rewriting `masters.ts` only.

Suggested local smoke-test before validation: `cd frontend && npm run dev` then visit `http://localhost:3000` → auto-redirects to `/admin/suppliers` with 3 seeded rows.
