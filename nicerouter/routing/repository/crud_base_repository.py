from abc import ABC, abstractmethod
from typing import Any, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, Select

class BaseCrudRepository[T: DeclarativeBase, ID: object](ABC):

    def __init__(self, session: AsyncSession, model_cls: type[T]) -> None: 
        self.session = session
        self.model_cls = model_cls

    @abstractmethod
    async def get_by_id(self, id: ID) -> T | None:
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        pass

    @abstractmethod
    async def get_many(self,
                       where_clause: Iterable[Any],
                       offset: int | None = None,
                       limit: int | None = None,) -> Iterable[T]:
        pass
 
    @abstractmethod
    async def delete_by_id(self, id: ID) -> bool:
        pass
  