from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    role: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    role: Literal["STAFF", "VERIFIER", "SUPERVISOR"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool


class UserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None
    new_password: str | None = Field(default=None, min_length=8)
