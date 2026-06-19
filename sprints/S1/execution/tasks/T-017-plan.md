# T-017 — Suppliers Router

**Module:** M-001 · **Depends on:** T-016 · **TC refs:** TC-033, TC-034 · **AC:** AC-001, AC-002

## Implementation logic

```python
# backend/src/presentation/api/routers/suppliers.py
from fastapi import APIRouter, Depends, Query, status

from src.application.services.supplier_service import SupplierService
from src.presentation.api.dependencies import get_supplier_service
from src.presentation.schemas.master import SupplierCreate, SupplierUpdate, SupplierRead

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    include_inactive: bool = Query(False),
    service: SupplierService = Depends(get_supplier_service),
):
    return service.list_suppliers(include_inactive=include_inactive)


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service),
):
    return service.create_supplier(payload)


@router.patch("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service),
):
    return service.update_supplier(supplier_id, payload)


@router.delete("/{supplier_id}", response_model=SupplierRead)
def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
):
    # DS-008: soft delete returns the deactivated row, not 204
    return service.deactivate_supplier(supplier_id)
```

## Constraints
- DS-008: DELETE returns the deactivated row (is_active=false), not 204 No Content
- DS-010: router is mounted under /api/v1 in main.py — prefix here is `/suppliers` only
- No business logic — all delegation to SupplierService

## Do not touch
Any other file.

## Success criteria
- **Manual:** `from src.presentation.api.routers.suppliers import router; print(router.routes)` -> 4 routes
- **Automated:** TC-033 (POST happy), TC-034 (DELETE soft)
- **DoD:** GET/POST/PATCH/DELETE all wired; POST returns 201

## Checkout prompt
*"Suppliers router — 4 endpoints, soft DELETE returns deactivated row."*
