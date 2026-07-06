from sqlalchemy import select

from src.infrastructure.db.models.auth import UserModel
from src.infrastructure.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):

    def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.username == username).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[UserModel]:
        stmt = (
            select(UserModel)
            .where(UserModel.is_active.is_(True))
            .order_by(UserModel.username.asc())
        )
        return list(self.session.execute(stmt).scalars())
