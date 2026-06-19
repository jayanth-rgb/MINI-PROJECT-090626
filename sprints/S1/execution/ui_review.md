# Sprint S1 — UI Review

**Produced by:** `/ases-ui-review S1`
**Critic:** Opus 4.7
**Companion JSON:** [ui_review.json](./ui_review.json)
**Reviewed spec:** [ui_spec.json](./ui_spec.json) · [ui_spec.md](./ui_spec.md)

---

## Headline

| | |
|---|---|
| **Verdict** | **APPROVED** |
| UI tasks reviewed | 15 (T-026 → T-040) |
| AC coverage | 13/13 UI-relevant ACs (100%) |
| Module boundary violations | 0 |
| API contract mismatches | 0 |
| Warnings | 5 (all non-blocking) |
| Gate | Unblocks `/ases-ui-scaffold S1` |

---

## Three checks

### 1. AC coverage — PASS

| AC | Component(s) addressing it |
|----|---------------------------|
| AC-001 | `SuppliersPage` + `SupplierForm` (T-035) — `supplier_name` + `place` required via `zodResolver(supplierSchema)` |
| AC-002 | `SuppliersPage` (T-035) — Deactivate row via `remove_mutation`; muted row rendering in `MasterDataTable`; reactivate via PATCH `is_active=true` |
| AC-004 | `StaffPage` + `StaffForm` (T-036) — `staff_name` required |
| AC-005 | `StaffPage` (T-036) — Deactivate via DELETE; future-S2 dropdown filter handled by backend `include_inactive=False` default |
| AC-007 | `DealersPage` + `DealerForm` (T-037) — `dealer_name` + `place` required |
| AC-008 | `DealersPage` (T-037) — Deactivate row |
| AC-011 | `GradesPage` (T-038) — 409 toast on duplicate `grade_code` (backend enforces UNIQUE) |
| AC-012 | `GradesPage` (T-038) — Deactivate row; `DesignGradeMapForm` grade Select filters to active only |
| AC-013 | `DesignsPage` + `DesignForm` (T-039) — `size` + `design_name` required |
| AC-015 | `DesignsPage` (T-039) — Deactivate row; `DesignGradeMapForm` design Select filters to active only |
| AC-016 | `DesignGradeMapPage` (T-040) — 409 toast on duplicate `(design_id, grade_id)` |
| AC-017 | `DesignGradeMapPage` (T-040) — Deactivate row preserves data |
| AC-019 | `designsApi.getGrades` (T-028) — DF-006 contract surface delivered for S2 even though no S1 page calls it |

**Backend-only ACs (correctly out of UI spec):** AC-003 / AC-006 / AC-009 / AC-010 / AC-014 / AC-018 — all covered by `seed_master_data.py` (T-025).

### 2. Module boundary — PASS

| Check | Result |
|-------|--------|
| UI module | M-006 (Frontend Application) |
| Dependencies invoked | M-001 only (in S1 scope) |
| M-002 (Transactions) endpoints | None |
| M-003 (Stock Ledger) endpoints | None |
| M-004 (Dashboard) endpoints | None |
| M-005 (Reports) endpoints | None |
| Direct DB access from frontend | None — all via `lib/api/masters.ts` |
| Admin shell nav | Limited to 6 master pages — no transactions/dashboard/reports routes leaked |

### 3. API contract — PASS

| Frontend wrapper | Endpoint | Backend router | Match |
|------------------|----------|----------------|-------|
| `suppliersApi` | `/suppliers` | T-017 `routers/suppliers.py` | ✓ |
| `staffApi` | `/staff` | T-018 `routers/staff.py` | ✓ |
| `dealersApi` | `/dealers` | T-019 `routers/dealers.py` | ✓ |
| `gradesApi` | `/grades` | T-020 `routers/grades.py` | ✓ |
| `designsApi` | `/designs` | T-021 `routers/designs.py` | ✓ |
| `designsApi.getGrades` | `/designs/{id}/grades` | T-021 `list_grades_for_design` | ✓ |
| `designGradeMapApi` | `/design-grade-map` | T-022 `routers/design_grade_map.py` | ✓ |

DTO field alignment: Supplier / Staff / Dealer / Grade / Design / DesignGradeMap / DesignGradeMin all match the LLD Pydantic Read schemas byte-for-byte. Versioning under `/api/v1` is consistent (encoded in `NEXT_PUBLIC_API_URL` per DS-010).

---

## Warnings (non-blocking — scaffold may proceed)

### W-001 · low · Error interceptor key precedence

**Where:** `ui_spec.plumbing_components.api_client.behavior.error_interceptor`

ui_spec prioritises `response.data.message` over `response.data.detail`. FastAPI's default HTTPException emits `{detail: '...'}` only. Backend `register_error_handlers` (T-008) does likewise.

**Fix during scaffold:** implement as `detail ?? message ?? error.message ?? 'Request failed'`. Align with LLD T-027 plan.md.

### W-002 · low · Reactivate path needs `is_active` in Update schemas

**Where:** `ui_spec.interaction_patterns.deactivate_flow`

Reactivate calls PATCH with `{ is_active: true }`. LLD Pydantic `SupplierUpdate` description says "All fields Optional" but doesn't explicitly include `is_active`. The service-layer dict-patch works (it just forwards keys), but the Pydantic Update schema should declare `is_active: bool | None`.

**Fix during /ases-dev T-007:** add `is_active: bool | None = None` to every `*Update` schema. The TS types in `ui_spec.plumbing_components.types_masters` already list `is_active?` correctly.

### W-003 · info · AC-019 contract unused by S1 admin UI

**Where:** `ui_spec.integration_points.s2_contract_delivered`

`designsApi.getGrades` is exposed but no S1 page calls it. AC-019 is covered at API + service test level (TC-031/032/036/037). This is intentional — the contract exists for S2 transaction forms.

**Action:** None — but /ases-ui-scaffold MUST still emit `designsApi.getGrades` in the integration boundary so S2 picks it up without rewriting `masters.ts`.

### W-004 · info · Mock 409 shape must match live backend

**Where:** `ui_spec.mock_strategy.scaffold_phase.boundary_during_scaffold`

The synthetic 409s thrown by scaffold-phase mocks (for TC-043 duplicate grade_code and TC-045 duplicate pair) must use the same `{status, detail}` shape as the live `apiClient` interceptor output.

**Fix during /ases-ui-scaffold:** mocks.ts must throw via `{ status: 409, detail: '(design_id, grade_id) already exists' }` so the toast handler is shape-agnostic across mock and integrated modes.

### W-005 · info · `is_active` column renderer not specified

**Where:** all `per_entity_pages.*.table_columns`

Every page lists an `is_active` column labelled 'Status', but `MasterDataTable` defaults to `String(row[key] ?? '')` rendering. The `status_rendering` block describes Active/Inactive Badge styles but doesn't tell the table how to invoke them for the `is_active` key.

**Fix during /ases-ui-scaffold:** either extend the `columns` prop with `render?: (row: T) => ReactNode`, or special-case `is_active` inside `MasterDataTable` to render the Badge. Pick one and apply uniformly across the 6 pages.

---

## What was checked but did NOT trigger a finding

- Sonner `Toaster` is mounted in root layout T-031 ✓
- TanStack Query staleTime (30s) + `refetchOnWindowFocus=false` per LLD ✓
- shadcn primitive list (Table, Dialog, Input, Label, Select, Button, Skeleton) — all in scaffold installed_packages ✓
- Sidebar nav items map 1:1 to /admin/{entity} routes ✓
- Test-id scheme consistent across pages (TC-039..TC-046 expect predictable selectors) ✓
- DS-011 form pattern (react-hook-form + Zod, no shadcn `form.tsx` shim) honored uniformly ✓
- Responsive breakpoints + mobile sidebar via Sheet — addresses DS-006 deployment expectations ✓

---

## Next step

→ **`/ases-ui-scaffold S1`** — Gemini builds the runnable Next.js scaffold from this spec. Five warnings above should be addressed inline during scaffold (W-001 + W-004 + W-005 most actionable for UI agent; W-002 is a backend-side fix carried into /ases-dev T-007 — log to context.json).
