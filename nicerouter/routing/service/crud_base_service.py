from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence, TypedDict, Unpack
from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from nicerouter.routing.service.dto_mapper import EntityDtoMapper
from nicerouter.routing.service.service_util import check_entity_found
from pydantic import BaseModel
from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
    BatchItem_ContainerType,
)
from sqlalchemy.ext.asyncio import AsyncSession

class GetManyParams(TypedDict, total=False):
    where_clause: Iterable[ColumnExpressionArgument[Any]]
    offset: int | None
    limit: int | None
    
class BaseCrudService[T: DeclarativeBase, ID: object](ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, id: ID) -> T | None:
        pass

    @abstractmethod
    async def save(self, session: AsyncSession, entity: T) -> T:
        pass

    @abstractmethod
    async def get_many(self, session: AsyncSession, params: GetManyParams) -> Iterable[T]:
        pass

    @abstractmethod
    async def delete_by_id(self, session: AsyncSession, id: ID) -> bool:
        pass

    @abstractmethod
    async def delete_multi(self, session: AsyncSession, id_list: Iterable[ID]) -> bool:
        pass

    @abstractmethod
    async def partial_update(
        self, session: AsyncSession, id: ID, updates: BaseModel
    ) -> T:
        pass

    @abstractmethod
    async def partial_update_multi(
        self,
        session: AsyncSession,
        update_list: BatchInputModel_ContainerType[ID, BaseModel],
    ) -> Sequence[T]:
        pass
