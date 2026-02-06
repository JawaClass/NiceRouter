from typing import Iterable, Sequence
from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.repository.crud_repository import CrudRepository
from nicerouter.routing.service.crud_base_service import BaseCrudService, GetManyParams
from nicerouter.routing.service.dto_mapper import EntityDtoMapper
from nicerouter.routing.service.service_util import check_entity_found
from pydantic import BaseModel
from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
)
from sqlalchemy.ext.asyncio import AsyncSession


class CrudService[T: DeclarativeBase, DTO: BaseModel](BaseCrudService[T, int]):
    def __init__(
        self, repository: CrudRepository[T], dto_mapper: EntityDtoMapper[DTO, T]
    ) -> None:
        self.repository = repository
        self.dto_mapper = dto_mapper

    async def get_by_id(self, session: AsyncSession, id: int) -> T | None:
        return await self.repository.get_by_id(session, id)

    async def get_by_id_with_options(
        self,
        session: AsyncSession,
        id: int,
        response_model: type[DTO],
        exclude_fields: list[str],
        max_depth: int,
    ) -> T | None:
        return await self.repository.get_by_id_with_options(
            session=session,
            id=id,
            response_model=response_model, # type: ignore
            exclude_fields=exclude_fields,
            id_field="id",
            max_depth=max_depth,
        )

    async def save(self, session: AsyncSession, entity: T) -> T:
        entity = await self.repository.save(session, entity)
        await session.commit()
        await session.refresh(entity)
        return entity

    async def create(self, session: AsyncSession, dto: DTO) -> T:
        entity = self.dto_mapper.dto2entity(dto)
        entity = await self.save(session=session, entity=entity)
        return entity

    async def delete_by_id(self, session: AsyncSession, id: int) -> bool:

        deleted = await self.repository.delete_by_id(session, id)

        if not deleted:
            raise RuntimeError(f"Entity with id {id=} not found.")

        await session.commit()

        return True

    async def delete_multi(self, session: AsyncSession, id_list: Iterable[int]) -> bool:
        for id in id_list:
            deleted = await self.repository.delete_by_id(session, id)
            if not deleted:
                raise RuntimeError(
                    f"Operation aborted. Cant delete entity with id {id=}. Please pass correct ids."
                )

        await session.commit()

        return True

    async def get_many(
        self, session: AsyncSession, params: GetManyParams
    ) -> Iterable[T]:

        result = await self.repository.get_many(
            session=session,
            limit=params.get("limit"),
            offset=params.get("offset"),
            options=params.get("options"),
            where_clause=params.get("where_clause"),
        )

        return result

    async def partial_update(
        self, session: AsyncSession, id: int, updates: BaseModel
    ) -> T:
        entity = await self.get_by_id(session, id)
        entity = check_entity_found(entity)

        for key, value in updates.model_dump(exclude_unset=True).items():  # type: ignore
            setattr(entity, key, value)

        entity = await self.save(session, entity)

        return entity

    async def partial_update_multi(
        self,
        session: AsyncSession,
        update_list: BatchInputModel_ContainerType[int, BaseModel],
    ):

        updated_entities: Sequence[T] = []
        for update_item in update_list.items:
            updated_entity = await self.partial_update(
                session=session, id=update_item.id, updates=update_item.data
            )
            updated_entities.append(updated_entity)

        return updated_entities
