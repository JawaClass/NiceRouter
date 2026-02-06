from abc import ABC, abstractmethod
from typing import Any, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


class BaseCrudRepository[T: DeclarativeBase, ID: object](ABC):

    def __init__(self, model_cls: type[T]) -> None:
        self.model_cls = model_cls

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, id: ID) -> T | None:
        pass

    @abstractmethod
    async def save(self, session: AsyncSession, entity: T) -> T:
        pass

    @abstractmethod
    async def get_many(
        self,
        session: AsyncSession,
        where_clause: Iterable[Any],
        offset: int | None = None,
        limit: int | None = None,
    ) -> Iterable[T]:
        pass

    @abstractmethod
    async def delete_by_id(self, session: AsyncSession, id: ID) -> bool:
        pass
