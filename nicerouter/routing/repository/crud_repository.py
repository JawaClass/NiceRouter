from typing import Any, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, load_only
from sqlalchemy import ColumnExpressionArgument, select, Select
from nicerouter.routing.param_builders import build_select_fields
from nicerouter.routing.repository.crud_base_repository import BaseCrudRepository
from nicerouter.routing.sa_select_in_deep import select_relationships_deep
from pydantic import BaseModel
from sqlalchemy.sql.base import ExecutableOption


def build_query_options[T: DeclarativeBase](
    db_class: type[T],
    exclude_fields: list[str],
    response_model: type[BaseModel],
    max_depth: int,
) -> list[ExecutableOption]:

    options: list[ExecutableOption] = []

    load_only_fields = build_select_fields(db_class, set(exclude_fields))
    if len(load_only_fields):
        options.append(load_only(*load_only_fields))

    nested_options = select_relationships_deep(
        db_class,
        response_model,
        exclude_field_names=set(exclude_fields),
        max_depth=max_depth,
    )

    options.extend(nested_options)

    return options


class CrudRepository[T: DeclarativeBase](BaseCrudRepository[T, int]):

    def __init__(self, model_cls: type[T]) -> None:
        super().__init__(model_cls=model_cls)

    async def get_by_id(
        self,
        session: AsyncSession,
        id: int,
        id_field: str = "id",
        options: Iterable[ExecutableOption] | None = None,
    ) -> T | None:
        db_class = self.model_cls
        stmt: Select[tuple[T]] = select(db_class)

        if options is not None:
            stmt = stmt.options(*options)

        id_column = getattr(db_class, id_field, None)

        if not id_column:
            raise RuntimeError(
                f"id_column {id_column=} does not exist on Entity {db_class.__name__}"
            )

        stmt = stmt.where(id_column == id)

        entity = await session.scalar(stmt)
        return entity

    async def save(self, session: AsyncSession, entity: T) -> T:
        # we dont commit here. trasnaction is handled by service layer
        instance = await session.merge(entity)
        return instance

    async def delete_by_id(self, session: AsyncSession, id: int) -> bool:
        entity = await self.get_by_id(session, id)
        if entity is None:
            return False

        await session.delete(entity)
        return True

    async def get_many(
        self,
        session: AsyncSession,
        where_clause: Iterable[ColumnExpressionArgument[Any]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        options: Iterable[ExecutableOption] | None = None,
    ) -> Iterable[T]:
        stmt: Select[tuple[T]] = select(self.model_cls)

        if options is not None:
            stmt = stmt.options(*options)

        if offset is not None:
            stmt = stmt.offset(offset=offset)

        if limit is not None:
            stmt = stmt.limit(limit=limit)

        if where_clause is not None:
            stmt = stmt.where(*where_clause)

        result = await session.scalars(stmt)
        result = result.all()
        return result

    async def get_by_id_with_options(
        self,
        session: AsyncSession,
        id: int,
        response_model: type[BaseModel],
        exclude_fields: list[str],
        max_depth: int,
        id_field: str = "id",
    ) -> T | None:

        db_class = self.model_cls

        options = build_query_options(
            db_class=db_class,
            exclude_fields=exclude_fields,
            max_depth=max_depth,
            response_model=response_model,
        )

        result = await self.get_by_id(
            session=session, id=id, id_field=id_field, options=options
        )

        return result
 