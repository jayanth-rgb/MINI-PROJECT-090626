from datetime import datetime, timedelta, timezone
import os

from jose import JWTError, jwt
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY not configured")
    expire_hours = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "8"))
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=expire_hours)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    secret_key = os.getenv("SECRET_KEY", "")
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except JWTError:
        return None
