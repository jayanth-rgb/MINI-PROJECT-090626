from fastapi import APIRouter, Depends, Query, status

from src.application.services.grade_service import GradeService
from src.presentation.api.dependencies import get_grade_service
from src.presentation.schemas.master import GradeCreate, GradeRead, GradeUpdate

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("", response_model=list[GradeRead])
def list_grades(
    include_inactive: bool = Query(False),
    service: GradeService = Depends(get_grade_service),
):
    return service.list_grades(include_inactive=include_inactive)


@router.post("", response_model=GradeRead, status_code=status.HTTP_201_CREATED)
def create_grade(
    payload: GradeCreate,
    service: GradeService = Depends(get_grade_service),
):
    return service.create_grade(payload)


@router.patch("/{grade_id}", response_model=GradeRead)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    service: GradeService = Depends(get_grade_service),
):
    return service.update_grade(grade_id, payload)


@router.delete("/{grade_id}", response_model=GradeRead)
def delete_grade(
    grade_id: int,
    service: GradeService = Depends(get_grade_service),
):
    return service.deactivate_grade(grade_id)
