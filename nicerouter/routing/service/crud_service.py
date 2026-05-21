from typing import Any, Iterable, Sequence

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.repository.crud_repository import (
    CrudRepository,
    build_query_options,
)
from nicerouter.routing.service.crud_base_service import BaseCrudService, GetManyParams
from nicerouter.routing.service.entity_mappers.mapper import ServiceEntityMapper
from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
)
from nicerouter.routing.service.service_util import check_entity_found
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputManyType,
    OutputType,
)


class CrudService[
    E: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
](BaseCrudService[E, int]):
    def __init__(
        self,
        repository: CrudRepository[E],
        entity_mapper: ServiceEntityMapper[E, Input, Output, OutputMany],
    ) -> None:
        self.repository = repository
        self.entity_mapper: ServiceEntityMapper[E, Input, Output, OutputMany] = (
            entity_mapper
        )

    async def get_by_id(self, session: AsyncSession, id: int) -> E | None:
        return await self.repository.get_by_id(session, id)

    async def get_by_id_with_options(
        self,
        session: AsyncSession,
        id: int,
        mask_class: type[BaseModel],
        exclude_fields: list[str],
        max_depth: int,
    ) -> E | None:
        entity = await self.repository.get_by_id_with_options(
            session=session,
            id=id,
            mask_class=mask_class,  # type: ignore
            exclude_fields=exclude_fields,
            id_field="id",
            max_depth=max_depth,
        )

        return entity

    async def save(self, session: AsyncSession, entity: E) -> E:
        entity = await self.repository.save(session, entity)
        await session.commit()
        await session.refresh(entity)
        return entity

    async def create(self, session: AsyncSession, dto: Input) -> E:
        entity = self.entity_mapper.input2entity(dto)
        entity = await self.save(session=session, entity=entity)
        return entity

    async def create_multi(
        self, session: AsyncSession, dto_list: list[Input]
    ) -> list[E]:
        created_entities: list[E] = []

        for dto in dto_list:
            entity = self.entity_mapper.input2entity(dto)
            entity = await self.repository.save(session, entity)
            created_entities.append(entity)

        await session.commit()

        for entity in created_entities:
            await session.refresh(entity)

        return created_entities

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
    ) -> Iterable[E]:

        db_class = self.repository.model_cls

        options = build_query_options(
            db_class=db_class,
            exclude_fields=params.get("exclude_fields") or [],
            max_depth=params.get("max_depth") or 0,
            mask_class=params.get("mask_class"),
        )

        result = await self.repository.get_many(
            session=session,
            limit=params.get("limit"),
            offset=params.get("offset"),
            options=options,
            where_clause=params.get("where_clause"),
        )

        return result

    async def partial_update(
        self, session: AsyncSession, id: int, updates: BaseModel
    ) -> E:
        entity = await self.get_by_id(session, id)
        entity = check_entity_found(entity)

        for key, value in updates.model_dump(exclude_unset=True).items():  # type: ignore
            setattr(entity, key, value)

        entity = await self.save(session, entity)

        return entity

    async def partial_update_multi(
        self,
        session: AsyncSession,
        # update_list: BatchInputModel_ContainerType[int, Input],
        update_list: BatchInputModel_ContainerType[int, Any],
    ):

        updated_entities: Sequence[E] = []
        for update_item in update_list.items:
            updated_entity = await self.partial_update(
                session=session, id=update_item.id, updates=update_item.data
            )
            updated_entities.append(updated_entity)

        return updated_entities
