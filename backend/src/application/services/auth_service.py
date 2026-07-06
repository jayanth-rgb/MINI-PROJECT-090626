from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.domain.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from src.infrastructure.db.models.auth import UserModel
from src.infrastructure.db.repositories.auth import UserRepository
from src.presentation.schemas.auth import TokenResponse, UserCreate, UserUpdate


class AuthService:

    def __init__(self, db: Session) -> None:
        self._repo = UserRepository(db)
        self._db = db

    def authenticate(self, username: str, password: str) -> TokenResponse:
        user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        token = create_access_token(data={"sub": user.username, "role": user.role})
        return TokenResponse(access_token=token, token_type="bearer", role=user.role)

    def get_current_user(self, token: str) -> UserModel:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return user

    def create_user(self, data: UserCreate) -> UserModel:
        if self._repo.get_by_username(data.username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.username}' already exists",
            )
        obj = self._repo.create({
            "username": data.username,
            "password_hash": get_password_hash(data.password),
            "role": data.role,
            "is_active": True,
        })
        self._db.commit()
        return obj

    def list_users(self) -> list[UserModel]:
        return self._repo.list_active()

    def get_user(self, user_id: int) -> UserModel:
        return self._repo.get(user_id)

    def update_user(self, user_id: int, data: UserUpdate) -> UserModel:
        patch: dict[str, Any] = {}
        if data.is_active is not None:
            patch["is_active"] = data.is_active
        if data.role is not None:
            patch["role"] = data.role
        if data.new_password is not None:
            patch["password_hash"] = get_password_hash(data.new_password)
        obj = self._repo.update(user_id, patch)
        self._db.commit()
        return obj

    def deactivate_user(self, user_id: int) -> UserModel:
        obj = self._repo.soft_delete(user_id)
        self._db.commit()
        return obj
