from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from fastapi import Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.types import EntiyType, InputType, OutputType
from nicerouter.routing.types import NiceAPIRoute


def create_post_route[Entiy: EntiyType, Input: InputType, Output: OutputType](
    *,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, Any],
    prefix: str,
    preprocessor_input: (
        Callable[[Input, AsyncSession], Awaitable[Input]] | None
    ) = None,
    postprocessor_output: (
        Callable[[Entiy, AsyncSession], Awaitable[Entiy]] | None
    ) = None,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, Any]:

    input_model = service.entity_mapper.input_cls
    output_model = service.entity_mapper.output_cls

    async def endpoint(
        payload: input_model,  # type: ignore
        db: AsyncSession = Depends(get_db_session),  # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        entity = await service.create(session=db, dto=payload)

        if postprocessor_output:
            entity = await postprocessor_output(entity, db)

        entity_as_output = service.entity_mapper.entity2output(entity)

        return entity_as_output

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}",
            methods=["POST"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=output_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )

    return route
