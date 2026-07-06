# Critique — T-088 · routers/report_export.py

**Iteration:** 1
**Verdict:** CLEAN
**File audited:** `backend/src/presentation/api/routers/report_export.py`

## Lens findings

### Lens 1 — Spec
Implementation matches `T-088-plan.json` and lld.json entry for `backend/src/presentation/api/routers/report_export.py`:
- Two GET routes present: `/sales/export` and `/inward/export`.
- Router `prefix='/reports'` and `tags=['export']` match the LLD `interfaces.exports` line (`APIRouter prefix='/reports', tags=['export']`).
- `format` declared as required Query with `regex='^(pdf|xlsx)$'` per LLD `functions[].inputs`.
- Optional filters (`date_from`, `date_to`, `dealer_ids`/`supplier_ids`, `places`, `design_ids`) match LLD signatures.
- No `response_model` on either route (required for binary StreamingResponse).
- Auth dependency `get_current_user` applied at route level per plan (any authenticated role).

### Lens 2 — Contract
- Exports `router` — matches LLD `interfaces.exports`.
- Imports resolve to existing symbols:
  - `get_current_user`, `get_report_export_service` from `src.presentation.api.dependencies` — both defined.
  - `ReportExportService.export_sales` / `export_inward` signatures match (format, date_from, date_to, list-or-None filters).
  - `UserModel` from `src.infrastructure.db.models.auth` — used only as a type annotation on the discarded auth dep.
- Return tuple destructured as `(buf, content_type, filename)` — matches service return contract `tuple[BytesIO, str, str]`.
- Mount order in `main.py` (line 65 before line 66) correctly places `report_export_router` BEFORE `inward_report_router` per the checkout_prompt.

### Lens 3 — Test
- TC-215 (`GET /reports/sales/export?format=pdf` → 200, `application/pdf`, `attachment` in Content-Disposition, body>0): satisfied — service returns `_PDF_MIME='application/pdf'` and router sets `Content-Disposition: attachment; filename=...`.
- TC-216 (`GET /reports/inward/export?format=xlsx` → 200, XLSX MIME): satisfied — service returns `_XLSX_MIME='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'`.
- AC-066 (unsupported format → 400): handled at `ReportExportService._validate_format`; router additionally rejects at the Query regex layer (defense in depth), returning 422 for schema violations. TC-215/216 do not exercise this path directly; T-087 owns TC-200.

### Lens 4 — Security
- Auth: `get_current_user` on both routes; unauthenticated requests hit 401 before service dispatch.
- Input validation: `format` constrained by regex; `dealer_ids`/`supplier_ids`/`design_ids` typed `list[int]` (Pydantic coerces); `date_from`/`date_to` typed `date`.
- Content-Disposition filename is server-generated as `{sales|inward}_report_{today}.{pdf|xlsx}` — no user-controlled substrings; response-splitting risk is nil.
- No secrets, no shell exec, no raw SQL in this layer.

### Lens 5 — Structural
Skipped — `graphify-out/graph.json` not referenced in scope.

## ADR alignment
- DS-007 (layering): router → service — no repository or ORM access at this layer.
- DS-018 (auth): OAuth2PasswordBearer JWT dependency reused via `get_current_user`.
- DS-021 (export stack): StreamingResponse wraps BytesIO returned by reportlab/openpyxl exporters through the service layer.

## Files reviewed
- `backend/src/presentation/api/routers/report_export.py` (implementation under audit)
- `backend/src/presentation/api/dependencies.py` (verifying `get_current_user` + `get_report_export_service`)
- `backend/src/application/services/report_export_service.py` (verifying return contract)
- `backend/src/main.py` (verifying mount order vs inward_report_router)
- `sprints/V2/design/lld.json` (LLD slice)
- `sprints/V2/design/test_cases.json` (TC-215, TC-216)
- `.ases/decisions.json` (DS-007, DS-018, DS-021 alignment)

## Verdict
CLEAN — no issues found across spec, contract, test, and security lenses.
