# Critique — T-066 (main.py MODIFY — mount 2 new routers)

**Sprint:** S3 · **Module:** M-002 · **Iteration:** 1 · **Verdict:** CLEAN

## Target
- `backend/src/main.py` (MODIFY)

## Lenses applied
- Lens 1 — Spec
- Lens 2 — Contract
- Lens 3 — Test
- Lens 4 — Security
- Lens 5 — Structural — SKIPPED (wiring-only modification adds no new functions/call-graph nodes)

## Decisions consulted (relevant subset)
| ID | Relevance |
|---|---|
| DS-001 | FastAPI stack — confirmed |
| DS-005 | V1 no auth — explains absence of auth on new mounts (not a defect) |
| DS-007 | 4-layer architecture — presentation layer mount only |
| DS-010 | `/api/v1` prefix — verified on both new mounts |

## Byte-identical preservation check (required regions)

| Region | Status | Location |
|---|---|---|
| `CORSMiddleware` block | PRESERVED | lines 25-31 |
| `register_error_handlers(app)` | PRESERVED | line 33 |
| `/health` endpoint | PRESERVED | lines 47-49 (returns `{"status": "ok"}`) |
| 9 existing `include_router` calls | PRESERVED | lines 35-43 (suppliers, staff, dealers, grades, designs, design_grade_map, inward, sales, adjustments — all `prefix="/api/v1"`) |

## New additions check

| Item | Status | Detail |
|---|---|---|
| Tuple-import alphabetical order | CORRECT | `adjustments, dashboard, dealers, design_grade_map, designs, grades, inward, sales, sales_report, staff, suppliers` (lines 6-18) |
| `dashboard` import position | CORRECT | After `adjustments`, before `dealers` (alphabetically right) |
| `sales_report` import position | CORRECT | After `sales`, before `staff` (alphabetically right) |
| `app.include_router(dashboard.router, prefix="/api/v1")` | CORRECT | Line 44 — appended after `adjustments` mount |
| `app.include_router(sales_report.router, prefix="/api/v1")` | CORRECT | Line 45 — appended after `dashboard` mount |
| Mount placement | APPENDED (not inserted mid-block) — matches plan + LLD files[9] |

## Lens-by-lens

### Lens 1 — Spec
Implementation matches `T-066-plan.json` scope exactly: 2 module names added to the alphabetized `routers` import tuple; 2 new `include_router` calls appended after `adjustments`. LLD files[9].functions[0].description ("Add app.include_router(dashboard.router, prefix='/api/v1') and app.include_router(sales_report.router, prefix='/api/v1') after the 9 existing mounts. No other changes.") is satisfied verbatim.

### Lens 2 — Contract
- Imports `dashboard` and `sales_report` from `src.presentation.api.routers` package.
- Verified `backend/src/presentation/api/routers/dashboard.py` exports `router = APIRouter(prefix="/dashboard", tags=["dashboard"])`.
- Verified `backend/src/presentation/api/routers/sales_report.py` exports `router = APIRouter(prefix="/reports/sales", tags=["reports"])`.
- Composed endpoints: `/api/v1/dashboard` and `/api/v1/reports/sales` — matches LLD `frontend_ui_track_note` integration-point contract.
- `depends_on` in plan (T-064 dashboard router, T-065 sales_report router) both satisfied — their `router` exports exist and are imported correctly.

### Lens 3 — Test
Task has no direct `test_case_refs[]` (wiring task). Transitively verified per `T-066-tests.md`:
- T-063 TC-159/TC-160 (DI graph)
- T-064 TC-117/TC-130/TC-131/TC-132 (`/api/v1/dashboard`)
- T-065 TC-140/TC-147/TC-148/TC-149/TC-158 (`/api/v1/reports/sales`)

A missing mount would surface as a 404 on every integration test that hits these endpoints — regression-immune.

### Lens 4 — Security
- No new attack surface introduced — wiring only.
- `CORSMiddleware` preserved with `allow_credentials=False` (correct posture given `allow_origins` may be `*` in dev).
- Per DS-005 (V1 ships without auth — internal-network only), the absence of auth on these new mounts is a documented PO decision, not a finding.

### Lens 5 — Structural (skipped)
Skipped — this MODIFY adds no new functions, only 2 import-tuple entries and 2 `include_router` lines. No call-graph nodes change.

## Findings
None.

## Summary
T-066 implementation is byte-identical-preserving for all required-untouched regions (CORS, `register_error_handlers`, `/health`, 9 existing mounts) and correctly adds the 2 new router mounts (`dashboard`, `sales_report`) under `prefix="/api/v1"` with alphabetical tuple-import placement. All 6 critical properties listed in the critique brief pass. S3 backend API surface is now fully wired.

## Next action
Proceed — T-066 complete.
