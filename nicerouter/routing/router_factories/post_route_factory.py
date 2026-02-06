from collections.abc import AsyncGenerator, Awaitable, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from sqlalchemy.orm import DeclarativeBase


def create_post_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    input_model: type[T_DTO],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
    preprocessor_input: (
        Callable[[T_DTO, AsyncSession], Awaitable[T_DTO]] | None
    ) = None,
    postprocessor_output: (
        Callable[[T_DB, AsyncSession], Awaitable[T_DB]] | None
    ) = None,
) -> NiceAPIRoute:

    async def endpoint(
        payload: input_model, # type: ignore
        db: AsyncSession = Depends(get_db_session),  # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)
        
        entity = await service.create(session=db, dto=payload)

        if postprocessor_output:
            entity = await postprocessor_output(entity, db)

        return entity

    route = NiceAPIRoute(
        route=APIRoute(path=f"{prefix}/{{id}}",
        methods=["POST"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,),
        service=service,
    )
    
    return route
