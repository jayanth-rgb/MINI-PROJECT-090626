# Sprint S2 — UI Review

**Reviewed by:** `/ases-ui-review` (Critic Opus) · **Date:** 2026-06-22 · **Verdict:** **APPROVED**

## 3-check summary

| # | Check | Result | Notes |
|---|---|---|---|
| 1 | `ac_coverage` | **pass** | 20/20 UI-relevant ACs addressed by components or validation rules |
| 2 | `module_boundary` | **pass** | All components in M-006 (Frontend); HTTP-only coupling to M-002 endpoints per DS-006 |
| 3 | `api_contract` | **pass** | 8 endpoints all map verbatim to LLD interfaces (T-046 schemas, T-047..050 services, T-052..055 routers) |

## Detailed AC coverage (20 ACs)

### F-007 Inward (8 ACs)
| AC | Component / mechanism | TC |
|---|---|---|
| AC-020 | InwardForm zod `purchase_date <= today` refinement | TC-090 |
| AC-021 | InwardForm zod `purchase_date >= today - 7d` refinement | TC-091 |
| AC-022 | Supplier MasterSelect → place ReadOnlyField | TC-092 |
| AC-023 | useGradesForDesign(design_id) → line field-array | TC-093 |
| AC-024 | zod `nos.refine(n => n === null \|\| n >= 0)` per line | TC-094 |
| AC-025 | Submit handler strips `nos == null \|\| 0` (client mirror of backend RULE-017) | — |
| AC-026 | zod `lines.refine(arr => arr.some(l => l.nos != null && l.nos > 0))` | TC-095 |
| AC-027 | mutation = single atomic submit; backend-enforced | — |

### F-008 Sales (6 ACs)
| AC | Component / mechanism | TC |
|---|---|---|
| AC-028 | SalesForm zod date refinements | TC-096 |
| AC-029 | Dealer MasterSelect → place ReadOnlyField | — |
| AC-030 | zod `loading_staff_id` + `verified_by_id` both `.int().positive()` required | TC-097 |
| AC-031 | useGradesForDesign(design_id) → line field-array | — |
| AC-032 | nos refinement per line (mirror of AC-024) | — |
| AC-033 | Backend invariant; UI submits payload | — |

### F-009 Adjustment (7 ACs)
| AC | Component / mechanism | TC |
|---|---|---|
| AC-034 | AdjustmentLineCreate type EXCLUDES design_id (only on header) — structurally enforced via T-046 mirror | — |
| AC-035 | zod cross-field `.refine(d => d.stock_date <= d.entry_date)` | TC-098 |
| AC-036 | useGradesWithCb pre-populates AdjustmentLineRow with software_cb read-only | TC-099 |
| AC-037 | zod `physical_cb.nonnegative()` per line | TC-100 |
| AC-038 | AdjustmentLineRow live-computed difference via `watch()` + aria-live='polite' | TC-101 |
| AC-039 | Backend invariant; UI submits payload | — |
| AC-040 | Err012Banner shown when getGradesWithCb returns `[]`; submit disabled | TC-102 |

**Total: 20/20 AC coverage. All 13 user-facing TCs (TC-090..TC-102) wired.**

## Module boundary review (HLD modules)

- **M-006 Frontend**: all UI components, hooks, api.ts, mocks.ts, types, schemas live in `frontend/src/`
- **M-002 Transaction Forms (backend)**: consumed via HTTP endpoints only (POST /inward, /sales, /adjustments; GET /designs/{id}/grades-with-cb). No direct import.
- **M-003 Stock Ledger Domain**: not reached by UI — composed transparently by M-002 endpoints server-side.
- **DS-006 honored**: frontend + backend as separate processes; HTTP is the only contract. No shared modules cross the tier boundary.

The Transactions nav sidebar addition modifies one existing S1 file in M-006 — within boundary. No cross-module touches.

## API contract verification

8 endpoints; all match LLD interfaces:

| Endpoint | Backend chain |
|---|---|
| POST `/api/v1/inward` | T-052 router → T-047 service → T-046 InwardCreate/Read |
| GET `/api/v1/inward` | T-052 + T-047 `list_inwards(date_from, date_to)` |
| POST `/api/v1/sales` | T-053 + T-048 + T-046 |
| GET `/api/v1/sales` | T-053 + T-048 `list_sales(date_from, date_to, dealer_ids?, design_ids?)` |
| POST `/api/v1/adjustments` | T-054 + T-049 + T-046 |
| GET `/api/v1/designs/{id}/grades-with-cb` | T-055 + T-050 + T-046 `DesignGradeReadWithCb` |
| GET `/api/v1/designs/{id}/grades` | S1 T-022 + T-006 (`DesignGradeReadMin`) |
| GET `/api/v1/{suppliers,dealers,staff,designs}` | S1 list endpoints |

Payload field-level correctness:
- `InwardCreate` has `purchase_date, supplier_id, entered_by_id, lines[]` — **NO place** (DS-013 / AC-022 server-derived) ✓
- `SalesCreate` has `sales_date, dealer_id, loading_staff_id, verified_by_id, lines[]` — **NO entered_by_id** (correct — different from Inward) ✓
- `AdjustmentCreate` has `stock_date, entry_date, design_id, entered_by_id, lines[]` ✓
- `AdjustmentLineCreate` has `grade_id, physical_cb` only — **NO software_cb** (server snapshots per AC-036) ✓
- `DesignGradeReadWithCb` is `{grade_id, grade_code, software_cb}` ✓

All payloads correctly drop fields that the backend computes/snapshots.

## Warnings (logged — non-blocking)

### UR-W007 — `GradeReadMin` vs `DesignGradeReadMin` naming
**Severity:** minor
**Component:** `InwardForm` + `SalesForm` useGradesForDesign + `mocks.ts`
The spec uses the placeholder name `GradeReadMin` for the S1 GET `/designs/{id}/grades` response. The actual S1 schema (verified in S1 `designs.py` imports) is named `DesignGradeReadMin`. Same shape (`{grade_id, grade_code}`), but the TS type and import should use the canonical name.

**Fix at scaffold time:** import `DesignGradeReadMin` from the S1 master schemas mirror (or re-export it via `types/master.ts`); do NOT define a parallel `GradeReadMin` alias. Update `mocks.ts` accordingly.

### UR-W008 — Reactivity of `useGradesWithCb` data → field-array
**Severity:** advisory
**Component:** `AdjustmentForm`
If the user changes `stock_date` AFTER selecting a design and the new date moves into a window with different active grades (or none), the line rows should re-populate / clear. The spec correctly gates the query on `(design_id && stock_date)`, but ensure the field-array reset is reactive to query refetch — not a one-shot populate.

**Fix at scaffold time:** Use `useEffect` on `data` change to call `form.reset({...form.getValues(), lines: newLines})` whenever `useGradesWithCb.data` updates. `Err012Banner` visibility binds directly to `data?.length === 0`, which is naturally reactive — no extra wiring there.

## Verdict

**APPROVED for scaffold.** Zero blocking issues. Two minor warnings logged — both resolvable at `/ases-ui-scaffold S2` time without redesign.

## Open questions

None.

→ Next: `/ases-ui-scaffold S2`
