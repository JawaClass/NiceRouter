from collections.abc import AsyncGenerator, Callable
from typing import Any, Awaitable

from fastapi import Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.types import EntiyType, InputType, OutputType
from nicerouter.routing.types import NiceAPIRoute


def create_delete_by_id_route[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    ResponseType,
](
    *,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, Any],
    prefix: str,
    response_model: ResponseType = None,
    preprocessor_input: (
        Callable[
            [int, AsyncSession, CrudService[Entiy, Input, Output, Any]], Awaitable[None]
        ]
        | None
    ) = None,
    postprocessor_output: (
        Callable[
            [bool, AsyncSession, CrudService[Entiy, Input, Output, Any]],
            Awaitable[ResponseType],
        ]
        | None
    ) = None,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, Any]:

    async def endpoint(
        id: int,
        db: AsyncSession = Depends(get_db_session),
    ):

        if preprocessor_input:
            await preprocessor_input(id, db, service)

        deleted = await service.delete_by_id(session=db, id=id)

        if not deleted:
            raise RuntimeError(
                f"Entity with id {id=} not found. Pass a existing id to delete."
            )

        response = None
        if postprocessor_output:
            response = await postprocessor_output(deleted, db, service)

        return response

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/{{id}}",
            methods=["DELETE"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=response_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )
    return route
