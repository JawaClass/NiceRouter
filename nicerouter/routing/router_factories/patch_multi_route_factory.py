from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any, Sequence

from fastapi import Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
)
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputType,
)
from nicerouter.routing.types import NiceAPIRoute

# type BatchInputModelAny = BatchInputModel_ContainerType[int, Any]


def create_patch_multi_route[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    ResponseType,
](
    *,
    response_model: ResponseType = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[
        Entiy,
        Input,
        Output,
        Any,
    ],
    prefix: str,
    preprocessor_input: (
        Callable[
            [BatchInputModel_ContainerType[int, Input], AsyncSession],
            Awaitable[BatchInputModel_ContainerType[int, Input]],
        ]
        | None
    ) = None,
    postprocessor_output: (
        Callable[[Sequence[Entiy], AsyncSession], Awaitable[ResponseType]] | None
    ) = None,
    **route_kwargs: Any,
) -> NiceAPIRoute:

    async def endpoint(
        payload: BatchInputModel_ContainerType[int, Input],
        db: AsyncSession = Depends(get_db_session),
    ):
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        updated_entities = await service.partial_update_multi(
            session=db, update_list=payload
        )

        if postprocessor_output:
            updated_entities = await postprocessor_output(updated_entities, db)

        return updated_entities

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/multi",
            methods=["PATCH"],
            tags=tags_from_prefix(prefix),  # type: ignore
            response_model=response_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )
    return route
