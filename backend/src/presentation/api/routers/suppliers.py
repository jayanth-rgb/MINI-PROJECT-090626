from fastapi import APIRouter, Depends, Query, status

from src.application.services.supplier_service import SupplierService
from src.presentation.api.dependencies import get_supplier_service
from src.presentation.schemas.master import SupplierCreate, SupplierRead, SupplierUpdate

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
    return service.deactivate_supplier(supplier_id)
