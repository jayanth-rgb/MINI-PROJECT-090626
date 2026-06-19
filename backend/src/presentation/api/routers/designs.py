from fastapi import APIRouter, Depends, Query, status

from src.application.services.design_grade_map_service import DesignGradeMapService
from src.application.services.design_service import DesignService
from src.presentation.api.dependencies import (
    get_design_grade_map_service,
    get_design_service,
)
from src.presentation.schemas.master import (
    DesignCreate,
    DesignGradeReadMin,
    DesignRead,
    DesignUpdate,
)

router = APIRouter(prefix="/designs", tags=["designs"])


@router.get("", response_model=list[DesignRead])
def list_designs(
    include_inactive: bool = Query(False),
    service: DesignService = Depends(get_design_service),
):
    return service.list_designs(include_inactive=include_inactive)


@router.post("", response_model=DesignRead, status_code=status.HTTP_201_CREATED)
def create_design(
    payload: DesignCreate,
    service: DesignService = Depends(get_design_service),
):
    return service.create_design(payload)


@router.patch("/{design_id}", response_model=DesignRead)
def update_design(
    design_id: int,
    payload: DesignUpdate,
    service: DesignService = Depends(get_design_service),
):
    return service.update_design(design_id, payload)


@router.delete("/{design_id}", response_model=DesignRead)
def delete_design(
    design_id: int,
    service: DesignService = Depends(get_design_service),
):
    return service.deactivate_design(design_id)


@router.get("/{design_id}/grades", response_model=list[DesignGradeReadMin])
def list_grades_for_design(
    design_id: int,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.list_active_grades_for_design(design_id)
