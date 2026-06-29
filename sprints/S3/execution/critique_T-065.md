# Critique — T-065 — `presentation/api/routers/sales_report.py`

**Iteration:** 1
**Verdict:** CLEAN
**Counts:** 0 critical / 0 major / 0 minor

## Scope verified
- File created: `backend/src/presentation/api/routers/sales_report.py` (28 LOC, single endpoint).
- Plan: `sprints/S3/execution/tasks/T-065-plan.json` + `T-065-plan.md`.
- LLD anchor: `sprints/S3/design/lld.json` files[6] (path `backend/src/presentation/api/routers/sales_report.py`).
- Test specs: TC-140, TC-147, TC-148, TC-149, TC-158 (load-bearing security TC).
- ADR anchor: DS-017 (shared filter predicate — inherited via service; router is pure delegation).

## Decisions cross-check
Read `.ases/decisions.json` first. DS-017 governs the service-layer shared filter predicate; the router is pure delegation and does not own that invariant. No DS-XXX entry forbids any property of this file. No tradeoff to flag.

## Lens 1 — Spec
| Property | Required | Actual | Result |
|---|---|---|---|
| `APIRouter(prefix=..., tags=...)` | `prefix="/reports/sales"`, `tags=["reports"]` | line 9 exact match | PASS |
| Single endpoint path | GET `""` (mounts as `/api/v1/reports/sales`) | `@router.get("", response_model=SalesReportResponse)` line 12 | PASS |
| `response_model` | `SalesReportResponse` | declared on decorator line 12 | PASS |
| Function name | `get_sales_report` | line 13 | PASS |
| Function signature | 5 query params + service Depends | lines 14-19 exact 1:1 with LLD inputs[] | PASS |
| Body | Single `return service.generate(...)` with all 5 kwargs | lines 21-27 — no other statements | PASS |
| No try/except | AssertionError from AC-050 bubbles to 500 | no try/except in file | PASS |

## Lens 2 — Contract
- Imports from `depends_on[]` are present and correctly used:
  - `SalesReportService` from `src.application.services.sales_report_service` — service exists, its `generate(...)` signature is `(date_from, date_to, dealer_ids, places, design_ids)`; router passes exactly those 5 kwargs.
  - `get_sales_report_service` from `src.presentation.api.dependencies` — factory exists (dependencies.py line 63).
  - `SalesReportResponse` from `src.presentation.schemas.sales_report` — schema exists with `consolidation: list[ConsolidationRow]` + `transactions: list[TransactionRow]`.
- `interfaces.exports = ["router (APIRouter prefix='/reports/sales', tags=['reports'])"]` — module-level `router` symbol exported on line 9. Consumed by T-066 (`main.py` mount) per LLD files[10].
- No dead imports; no unused symbols.

## Lens 3 — Test
| TC | Property under test | Implementation support |
|---|---|---|
| TC-140 | GET /api/v1/reports/sales → 200 with `{consolidation, transactions}` | `response_model=SalesReportResponse` serializes both keys |
| TC-147 | No-filter call → 200 full dataset | All 5 params default to `None`; forwarded unchanged to service |
| TC-148 | All 5 filters set simultaneously → 200 filtered | All 5 kwargs forwarded by name; no parameter is silently dropped |
| TC-149 | `?date_from=not-a-date` → 422 | `date_from: date \| None = Query(default=None)` — FastAPI built-in date parsing returns 422 on malformed input |
| **TC-158** | `?places=' OR 1=1--` → 200, 0 rows, no SQL injection | Router does NO string interpolation; raw string list is passed unchanged through `service.generate(places=...)` where T-062's `_build_filters` uses SQLAlchemy `.in_()` parameter binding — the literal `' OR 1=1--` is bound as a parameter value, not interpolated into SQL |

All 5 TCs are satisfied by the implementation as written.

## Lens 4 — Security
- **No string interpolation, no raw SQL** in this file. The router does not touch the SQL layer.
- **Input validation present**: FastAPI parses + validates `date | None`, `list[int] | None`, `list[str] | None` at request time. Malformed dates / non-int dealer_ids / non-int design_ids all yield 422 before any service call (covers TC-149).
- **SQL-injection vector (TC-158)**: untrusted query-string values (e.g., `places=' OR 1=1--`) flow into Python `list[str]` and are passed by keyword to `SalesReportService.generate(places=...)`. The service then uses these via SQLAlchemy `.in_()`, which produces a parameterised `IN (:param_1, :param_2, ...)` clause with values bound through the DB driver. The literal string is therefore matched as a string against `place_snapshot`, NOT interpolated into the SQL — verified by inspection of the service file (lines 1-60) which imports from `sqlalchemy` core and uses `select(...)` + `func` rather than `text()`.
- **No try/except** — `AssertionError` raised by service AC-050 reconciliation correctly bubbles to FastAPI's default 500 handler (intentional per plan §Constraints; indicates real data corruption that must be loud).
- **No secrets** in router; no logging of request bodies; no `print` statements.
- **No authentication required** — consistent with DS-005 (V1 ships without auth; closed-network deployment).

## Lens 5 — Structural
`graphify-out/graph.json` not in scope for this critique (the file is excluded per CLAUDE.md repository layout note and not referenced by the task). Lens skipped per critique rules.

## Reference-pattern parity
The implementation is byte-equivalent in structure to T-053's `routers/sales.py::list_sales` (the explicit reference pattern called out in the plan and LLD purpose field):
- Same decorator shape (`@router.get("", response_model=...)`).
- Same `date | None = Query(default=None)` for dates.
- Same `list[int] | None = Query(default=None)` for ID lists (native repeat-key parsing — no comma-splitting, no `Query(...)` strict-required pattern, no manual parsing helpers).
- Same single-line `return service.<method>(...)` delegation body.

No deviations.

## Summary
Pure delegation router with exact LLD/plan compliance. All 5 critique lenses pass with zero issues at any severity. TC-158 (the load-bearing SQL-injection security test) is satisfied by FastAPI's typed parameter binding plus SQLAlchemy `.in_()` parameterisation downstream — the router contributes no injection surface of its own. Ready for T-066 mount.
