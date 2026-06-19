# Critique — T-017 Suppliers Router

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/presentation/api/routers/suppliers.py` (41 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — router delegates fully to service; no DB or domain logic
- **DS-008** soft delete — DELETE returns the deactivated row (`response_model=SupplierRead`), not 204
- **DS-010** API versioning — router prefix is `/suppliers` only; `/api/v1` prepended in `main.py`

## Lens 1 — Spec
LLD `files[16]` parity:
- `list_suppliers(include_inactive, service)` ✓
- `create_supplier(payload, service)` — `status_code=201` ✓
- `update_supplier(supplier_id, payload, service)` — PATCH ✓
- `delete_supplier(supplier_id, service)` — returns SupplierRead (soft) ✓

Router: `APIRouter(prefix="/suppliers", tags=["suppliers"])` ✓.

## Lens 2 — Contract
Imports vs `depends_on = ["T-016"]`:
- T-016 → `get_supplier_service` ✓
- T-010 (transitive via T-016) → `SupplierService` (typed annotation only) ✓
- T-007 → `SupplierCreate / SupplierRead / SupplierUpdate` ✓
- `fastapi.{APIRouter, Depends, Query, status}` ✓

Exports: module-level `router` ✓ — matches LLD `interfaces.exports = ["router (APIRouter prefix='/suppliers', tags=['suppliers'])"]`.

## Lens 3 — Test
- **TC-033** (AC-001, POST 201 + body shape): `@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)` returns service result. FastAPI serializes via `SupplierRead` → body has `{supplier_id, supplier_name, place, is_active, created_at}` and `is_active=true` (server_default). ✓
- **TC-034** (AC-002, DELETE 200 + soft): `@router.delete("/{supplier_id}", response_model=SupplierRead)` (default 200) returns `service.deactivate_supplier(id)` which sets `is_active=False` and commits without deleting the row (DS-008). Body shape SupplierRead with `is_active: false`. ✓

## Lens 4 — Security
- All persistence delegated to service → repo → ORM (parameterized) ✓
- Path param `supplier_id: int` is auto-coerced + rejected on non-int by FastAPI before service is called ✓
- Body bound to `SupplierCreate / SupplierUpdate` — Pydantic `min_length=1` enforces AC-001 ✓
- No CORS or auth at router level — DS-005 V1 limitation ADR-tracked ✓
- `response_model` strips any extra attributes from ORM objects — prevents accidental field leakage ✓

## Lens 5 — Structural
- Imported by `main.py` (T-023) — `app.include_router(suppliers.router, prefix="/api/v1")` ✓
- All 4 routes reachable from FastAPI; OpenAPI will list `GET/POST/PATCH/DELETE /api/v1/suppliers[/{id}]` ✓

## Verdict
**CLEAN** — exact 4-endpoint shape; soft DELETE returns the deactivated row per DS-008; both critical TCs (TC-033, TC-034) satisfied. Proceed.
