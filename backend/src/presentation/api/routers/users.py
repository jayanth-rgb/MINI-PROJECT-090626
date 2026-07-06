from fastapi import APIRouter, Depends, status

from src.presentation.api.dependencies import get_auth_service, require_supervisor
from src.application.services.auth_service import AuthService
from src.presentation.schemas.auth import UserCreate, UserRead, UserUpdate
from src.infrastructure.db.models.auth import UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.create_user(payload)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    return svc.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    svc: AuthService = Depends(get_auth_service),
    _: UserModel = Depends(require_supervisor),
):
    svc.deactivate_user(user_id)
    return None
