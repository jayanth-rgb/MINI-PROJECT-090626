from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.exceptions import NotFoundError
from src.infrastructure.db.base import Base

TModel = TypeVar("TModel", bound=Base)


class BaseRepository(Generic[TModel]):
    model: Type[TModel]

    def __class_getitem__(cls, model: Type[TModel]):
        # Bind self.model when subclassing:
        # class FooRepository(BaseRepository[FooModel]) -> FooRepository.model = FooModel
        new_cls = type(
            f"BaseRepository[{model.__name__}]",
            (cls,),
            {"model": model},
        )
        return new_cls

    def __init__(self, session: Session):
        self.session = session

    def list(self, include_inactive: bool = False) -> list[TModel]:
        stmt = select(self.model)
        if not include_inactive:
            stmt = stmt.where(self.model.is_active.is_(True))
        return list(self.session.execute(stmt).scalars())

    def get(self, id_: int) -> TModel:
        obj = self.session.get(self.model, id_)
        if obj is None:
            raise NotFoundError(self.model.__name__.removesuffix("Model"), id_)
        return obj

    def create(self, data: dict[str, Any]) -> TModel:
        obj = self.model(**data)
        self.session.add(obj)
        self.session.flush()
        return obj

    def update(self, id_: int, patch: dict[str, Any]) -> TModel:
        obj = self.get(id_)
        for k, v in patch.items():
            if v is not None:
                setattr(obj, k, v)
        self.session.flush()
        return obj

    def soft_delete(self, id_: int) -> TModel:
        obj = self.get(id_)
        obj.is_active = False
        self.session.flush()
        return obj
