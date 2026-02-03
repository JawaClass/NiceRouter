from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence 
from sqlalchemy.orm import DeclarativeBase 
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from nicerouter.routing.service.dto_mapper import EntityDtoMapper
from nicerouter.routing.service.service_util import check_entity_found
from pydantic import BaseModel
from nicerouter.routing.service.model_types import BatchInputModel_ContainerType, BatchItem_ContainerType

class BaseCrudService[T: DeclarativeBase, ID: object](ABC):
 
    # def __init__(self, repository: BaseCrudRepository[T, ID], dto_mapper: EntityDtoMapper) -> None: 
    #     pass
        # # Every subclass will now have these attributes automatically
        # self.repository = repository 
        # self.dto_mapper = dto_mapper

    @abstractmethod
    async def get_by_id(self, id: ID) -> T | None:
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        pass

    @abstractmethod
    async def get_many(self) -> T:
        pass
 
    @abstractmethod
    async def delete_by_id(self, id: ID) -> bool:
        pass
    
    @abstractmethod
    async def delete_multi(self, id_list: Iterable[ID]) -> bool:
        pass

    @abstractmethod
    async def partial_update(self, id: ID, updates: BaseModel) -> T:
        pass
    
    @abstractmethod
    async def partial_update_multi(self, update_list: BatchInputModel_ContainerType[ID, BaseModel]) -> Sequence[T]:
        pass
 