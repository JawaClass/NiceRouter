from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence 
from sqlalchemy.orm import DeclarativeBase 
from nicerouter.routing.param_builders import build_exclude_fields_set, build_select_fields
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from nicerouter.routing.repository.crud_repository import CrudRepository
from nicerouter.routing.service.crud_base_service import BaseCrudService
from nicerouter.routing.service.service_util import check_entity_found
from pydantic import BaseModel
from nicerouter.routing.service.model_types import BatchInputModel_ContainerType, BatchItem_ContainerType
from sqlalchemy.orm import DeclarativeBase, load_only, Load


class CrudService[T: DeclarativeBase](BaseCrudService[T, int]):

    def __init__(self, repository: CrudRepository[T]) -> None:
        super().__init__(repository)
        self.repository = repository

    async def get_by_id(self, id: int) -> T | None:
        return await self.repository.get_by_id(id)
    
    async def get_by_id_with_options(self, id: int, response_model: type[BaseModel], exclude_fields: list[str], max_depth: int) -> T | None:
        return await self.repository.get_by_id_with_options(
            id=id,
            response_model=response_model,
            exclude_fields=exclude_fields,
            id_field="id",
            max_depth=max_depth
        )

    async def save(self, entity: T) -> T:
        instance = await self.repository.save(entity)
        await self.repository.session.commit()
        await self.repository.session.refresh(entity)
        return instance
    
    async def delete_by_id(self, id: int) -> bool:

        deleted = await self.repository.delete_by_id(id)

        if not deleted:
            raise RuntimeError(f"Entity with id {id=} not found.")

        await self.repository.session.commit()
        
        return True

    async def delete_multi(self, id_list: Iterable[int]) -> bool:
        for id in id_list:
            deleted = await self.repository.delete_by_id(id)
            if not deleted:
                raise RuntimeError(f"Operation aborted. Cant delete entity with id {id=}. Please pass correct ids.")

        await self.repository.session.commit()

        return True
    
    async def get_many(self, 
                       where_clause: Iterable[Any],
                       offset: int | None = None,
                       limit: int | None = None, 
                       ) -> Iterable[T]:
        
        result = await self.repository.get_many(where_clause=where_clause, offset=offset, limit=limit)
        
        return result
    
    async def partial_update(self, id: int, updates: BaseModel) -> T:
        entity = await self.get_by_id(id)
        entity = check_entity_found(entity)
        
        for key, value in updates.model_dump(exclude_unset=True).items():  # type: ignore
                setattr(entity, key, value)

        entity = await self.save(entity)

        return entity
    
    async def partial_update_multi(self, update_list: BatchInputModel_ContainerType[int, BaseModel]):

        updated_entities: Sequence[T] = []
        for update_item in update_list.items:
            
            updated_entity = await self.partial_update(id=update_item.id, updates=update_item.data)
            updated_entities.append(updated_entity)

        return updated_entities