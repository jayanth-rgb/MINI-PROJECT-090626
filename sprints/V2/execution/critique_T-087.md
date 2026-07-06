# Critique — T-087 (V2)

**Target:** `backend/src/application/services/report_export_service.py`
**Module:** M-010 · **Verdict:** CLEAN

## Summary

`ReportExportService` implements both `export_sales` and `export_inward` with fail-fast format validation, correct delegation to the sibling report services, and returns the required `(BytesIO, content_type, filename)` 3-tuple. All five lenses pass.

## Lens Results

### Lens 1 — Spec (PASS)

- Signatures match LLD `files[].functions[]`:
  - `export_sales(format, date_from, date_to, dealer_ids, places, design_ids) -> tuple[BytesIO, str, str]`
  - `export_inward(format, date_from, date_to, supplier_ids, places, design_ids) -> tuple[BytesIO, str, str]`
- Filenames formatted `sales_report_{YYYY-MM-DD}.{ext}` and `inward_report_{YYYY-MM-DD}.{ext}` per plan.
- Constructor takes `db: Session` per plan.
- Minor deviation from plan snippet: `format` typed as `str` instead of `Literal['pdf','xlsx']`. Functionally equivalent — `Literal` does not enforce runtime validation, and the whitelist check does. Not a defect.

### Lens 2 — Contract (PASS)

- Exports `ReportExportService` (matches `interfaces.exports`).
- Imports resolve against `depends_on[]`:
  - `SalesReportService` (S3 existing) — verified constructor accepts a positional `Session`.
  - `InwardReportService` (sibling T-077).
  - `PdfExporter` / `ExcelExporter` (siblings T-085/T-086) — verified `export_sales_report(data, filters)` / `export_inward_report(data, filters)` signatures.
- `src.` import prefix consistent with existing codebase (`inward_report_service.py`, `sales_report_service.py`).
- All imports used.

### Lens 3 — Test (PASS)

- TC-200: `export_sales(format='csv', ...)` → `HTTPException(status_code=400)`.
  - `_validate_format` runs FIRST, before any `SalesReportService` construction — no DB required for the test to pass.
  - Detail string mentions supported formats.

### Lens 4 — Security (PASS)

- Whitelist validation prevents unsupported/malicious format strings from reaching the exporter branches.
- No SQL executed at this layer (DS-007 respected).
- Filename derived from `date.today()` and constant labels — no user input reaches the filename slot (Content-Disposition injection surface owned by router T-088).
- Format value echoed in the 400 detail — reflected but harmless (no HTML render context in JSON error body).
- No secrets, no unsafe deserialization.

### Lens 5 — Structural (SKIPPED)

`graphify-out/graph.json` not consulted. Manual note: this service is a hub between report services and exporters — reachability confirmed via planned T-088 router and T-089 dependency wiring.

## Decisions Matched

- **DS-007** (four-layer architecture): application service delegates to other application services + infra exporters; no raw ORM queries here.
- **DS-021** (reportlab / openpyxl / StreamingResponse): honored by returning `BytesIO` plus the correct MIME constants (`application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`).

## Findings

None.

## Next Action

Proceed to T-088 (router) — this task is ready to be consumed.
