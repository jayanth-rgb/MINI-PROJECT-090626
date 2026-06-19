from fastapi import APIRouter, Depends, Query, status

from src.application.services.design_grade_map_service import DesignGradeMapService
from src.presentation.api.dependencies import get_design_grade_map_service
from src.presentation.schemas.master import (
    DesignGradeMapCreate,
    DesignGradeMapRead,
    DesignGradeMapUpdate,
)

router = APIRouter(prefix="/design-grade-map", tags=["design-grade-map"])


@router.get("", response_model=list[DesignGradeMapRead])
def list_mappings(
    include_inactive: bool = Query(False),
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.list_mappings(include_inactive=include_inactive)


@router.post(
    "",
    response_model=DesignGradeMapRead,
    status_code=status.HTTP_201_CREATED,
)
def create_mapping(
    payload: DesignGradeMapCreate,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.create_mapping(payload)


@router.patch("/{map_id}", response_model=DesignGradeMapRead)
def update_mapping(
    map_id: int,
    payload: DesignGradeMapUpdate,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.update_mapping(map_id, payload)


@router.delete("/{map_id}", response_model=DesignGradeMapRead)
def delete_mapping(
    map_id: int,
    service: DesignGradeMapService = Depends(get_design_grade_map_service),
):
    return service.deactivate_mapping(map_id)
