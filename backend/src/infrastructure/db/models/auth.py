from sqlalchemy import Boolean, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base, TimestampMixin


class UserModel(Base, TimestampMixin):
    __tablename__ = "tbl_user_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("STAFF", "VERIFIER", "SUPERVISOR", name="user_role_enum"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_user_master_username", "username"),
    )
