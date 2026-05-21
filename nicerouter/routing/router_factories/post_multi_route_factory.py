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
    OutputManyType,
    OutputType,
)
from nicerouter.routing.types import NiceAPIRoute


def create_post_multi_route[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
](
    *,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, OutputMany],
    prefix: str,
    preprocessor_input: (
        Callable[[list[Input], AsyncSession], Awaitable[list[Input]]] | None
    ) = None,
    postprocessor_output: (
        Callable[[list[Entiy], AsyncSession], Awaitable[list[Entiy]]] | None
    ) = None,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, OutputMany]:

    input_model = service.entity_mapper.input_cls

    async def endpoint(
        payload: list[input_model],  # type: ignore
        db: AsyncSession = Depends(get_db_session),  # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        entity_list = await service.create_multi(session=db, dto_list=payload)

        if postprocessor_output:
            entity_list = await postprocessor_output(entity_list, db)

        entity_list_as_output = service.entity_mapper.entities2output(entity_list)
        return entity_list_as_output

    response_model = service.entity_mapper.output_many_cls

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/multi",
            methods=["POST"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=response_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )

    return route
