from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from fastapi import Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputType,
)
from nicerouter.routing.types import NiceAPIRoute


def create_patch_route[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    ResponseType,
](
    *,
    # input_model: type[T_IN],
    # response_model: Any,
    response_model: ResponseType = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, Any],
    prefix: str,
    preprocessor_input: (
        Callable[[Input, AsyncSession], Awaitable[Input]] | None
    ) = None,
    postprocessor_output: (
        Callable[[Entiy, AsyncSession], Awaitable[ResponseType]] | None
    ) = None,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, Any]:

    input_model = service.entity_mapper.input_cls

    async def endpoint(
        id: int,
        payload: input_model,  # type: ignore
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
            **route_kwargs,
        ),
        service=service,
    )
    return route
