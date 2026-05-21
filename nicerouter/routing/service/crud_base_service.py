from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence, TypedDict

from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
)


class GetManyParams(TypedDict, total=True):
    where_clause: Iterable[ColumnExpressionArgument[Any]]
    offset: int | None
    limit: int | None
    mask_class: type[BaseModel]
    max_depth: int | None
    exclude_fields: list[str] | None


class BaseCrudService[T: DeclarativeBase, ID: object](ABC):
    @abstractmethod
    async def get_by_id(self, session: AsyncSession, id: ID) -> T | None:
        pass

    @abstractmethod
    async def save(self, session: AsyncSession, entity: T) -> T:
        pass

    @abstractmethod
    async def get_many(
        self, session: AsyncSession, params: GetManyParams
    ) -> Iterable[T]:
        pass

    @abstractmethod
    async def delete_by_id(self, session: AsyncSession, id: ID) -> bool:
        pass

    @abstractmethod
    async def delete_multi(self, session: AsyncSession, id_list: Iterable[ID]) -> bool:
        pass

    @abstractmethod
    async def partial_update[UPDATE: BaseModel](
        self, session: AsyncSession, id: ID, updates: UPDATE
    ) -> T:
        pass

    @abstractmethod
    async def partial_update_multi[UPDATE: BaseModel](
        self,
        session: AsyncSession,
        update_list: BatchInputModel_ContainerType[ID, UPDATE],
    ) -> Sequence[T]:
        pass
