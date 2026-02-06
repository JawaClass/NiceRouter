from collections.abc import AsyncGenerator, Awaitable, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from sqlalchemy.orm import DeclarativeBase


def create_post_multi_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    input_model: type[T_DTO],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
    preprocessor_input: (
        Callable[[list[T_DTO], AsyncSession], Awaitable[list[T_DTO]]] | None
    ) = None,
    postprocessor_output: (
        Callable[[list[T_DB], AsyncSession], Awaitable[list[T_DB]]] | None
    ) = None,
) -> NiceAPIRoute:

    async def endpoint(
        payload: list[input_model], # type: ignore
        db: AsyncSession = Depends(get_db_session),  # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)
        
        entity_list = await service.create_multi(session=db, dto_list=payload)

        if postprocessor_output:
            entity_list = await postprocessor_output(entity_list, db)

        from nicerouter.sa_to_dict import sa_to_dict
        entity_list = sa_to_dict(entity_list)
        return entity_list

    route = NiceAPIRoute(
        route=APIRoute(path=f"{prefix}/multi",
        methods=["POST"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=list[response_model],
        endpoint=endpoint,),
        service=service,
    )
    
    return route
