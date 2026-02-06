from collections.abc import AsyncGenerator, Awaitable, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from sqlalchemy.orm import DeclarativeBase


def create_patch_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    input_model: type[T_DTO],
    response_model: type[T_DTO],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
    preprocessor_input: (
        Callable[[BaseModel, AsyncSession], Awaitable[BaseModel]] | None
    ) = None,
    postprocessor_output: (
        Callable[[T_DB, AsyncSession], Awaitable[T_DB]] | None
    ) = None,
) -> NiceAPIRoute:

    async def endpoint(
        id: int,
        payload: input_model, # type: ignore
        db: AsyncSession = Depends(get_db_session),
    ): 
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        updated_entity = await service.partial_update(
            session=db, id=id, updates=payload
        )

        if postprocessor_output:
            updated_entity = await postprocessor_output(updated_entity, db)

        return updated_entity

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/{{id}}",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,
        ),
        service=service,
    )
    return route
