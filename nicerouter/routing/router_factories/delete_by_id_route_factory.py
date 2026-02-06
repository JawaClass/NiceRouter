from collections.abc import AsyncGenerator, Callable
from typing import Awaitable
from fastapi import Depends, Response
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from sqlalchemy.orm import DeclarativeBase

from nicerouter.routing.service.crud_base_service import BaseCrudService


def create_delete_by_id_route[T_DB: DeclarativeBase](
    *,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: BaseCrudService[T_DB, int],
    prefix: str,
    preprocessor_input: (Callable[[int, AsyncSession], Awaitable[None]] | None) = None,
    postprocessor_output: (
        Callable[[bool, AsyncSession], Awaitable[None]] | None
    ) = None,
) -> NiceAPIRoute:

    async def endpoint(
        id: int,
        db: AsyncSession = Depends(get_db_session),
    ):

        if preprocessor_input:
            await preprocessor_input(id, db)

        deleted = await service.delete_by_id(session=db, id=id)

        if not deleted:
            raise RuntimeError(
                f"Entity with id {id=} not found. Pass a existing id to delete."
            )

        if postprocessor_output:
            await postprocessor_output(deleted, db)

        return Response()

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/{{id}}",
            methods=["DELETE"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=None,
            endpoint=endpoint,
        ),
        service=service,
    )
    return route
