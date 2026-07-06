# Critique — T-091 · routers/invoices.py

**Sprint:** V2 · **Module:** M-011 · **Verdict:** CLEAN

## Summary
`backend/src/presentation/api/routers/invoices.py` implements all 4 endpoints per the task plan and DS-023:

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/invoices` (+ filters) | any-auth | `list[InvoiceSummary]` |
| POST | `/invoices?sales_header_id=N` | SUPERVISOR | `InvoiceRead` (201) |
| GET | `/invoices/{invoice_id}` | any-auth | `InvoiceRead` |
| POST | `/invoices/{invoice_id}/payments` | SUPERVISOR | `InvoiceRead` (201) |

InvoiceService is wired via `Depends(get_invoice_service)`. 4-route manual check will pass.

## Lens results

### Lens 1 — Spec (pass)
Routes, response models, status codes, and auth guards all match the plan. Note the plan snippet showed `svc.record_payment(invoice_id, payload.amount)` but the actual `InvoiceService.record_payment` signature expects `PaymentCreate`. Implementation correctly forwards the full `payload` object (see `invoice_service.py:167`). This is a reconciliation of the plan snippet, not a defect.

### Lens 2 — Contract (pass)
All imports resolve to files produced by declared upstream tasks (T-076, T-082, T-084, T-089). Exports (`router`) match the mount expected by `main.py`. No dead imports.

### Lens 3 — Test (pass)
TC-217 (integration) will be satisfied: the router is a pure delegation to `InvoiceService.create_from_sales`, which builds the `INV-YYYYMMDD-NNNNN` number, computes `total_amount` from snapshot prices, and returns status='PENDING'. The 4xx exceptions the service raises (404, 409, 422) propagate transparently.

### Lens 4 — Security (pass)
- Auth: `Depends(get_current_user)` on reads, `Depends(require_supervisor)` on writes (DS-018/DS-019).
- Input validation: `int` typing on ids, regex on `status` filter (`^(PENDING|PARTIAL|PAID)$`), schema-level `gt=0` on `PaymentCreate.amount`.
- No SQL interpolation in this file; DB access is fully via the service layer.

### Lens 5 — Structural (skipped)
`graphify-out/graph.json` not consulted; router will be reachable via `main.py` include_router in T-093.

## Findings (2 minor, non-blocking)

**F-1 — minor · readability**
`list_invoices` declares `status: str | None = Query(...)`, shadowing the imported `fastapi.status` module inside the function. No runtime bug (decorators evaluate before the parameter binds, and the body doesn't reference the module), but it is a mild readability trap. Optional rename to `status_filter` or `import status as http_status`.

**F-2 — minor · spec-divergence (ADR tradeoff)**
The LLD text for `create_invoice` describes `sales_header_id` as JSON body, but the task plan overrides this to `Query(...)` per DS-023 and TC-217's request body carries only `sales_header_id`. Implementation follows the plan (Query param). No code fix; recommend a future LLD refresh align the annotation.

## Counts
| Severity | Count |
|---|---|
| critical | 0 |
| major | 0 |
| minor | 2 |
