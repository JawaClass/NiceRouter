from collections.abc import AsyncGenerator, Awaitable, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.routes_service import tags_from_prefix
from sqlalchemy.orm import DeclarativeBase
from typing import Any, Sequence
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.model_types import (
    BatchInputModel_ContainerType,
)

type BatchInputModelAny = BatchInputModel_ContainerType[int, Any]


def create_patch_multi_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    input_model: type[BaseModel],
    response_model: T_DTO,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
    preprocessor_input: (
        Callable[[BatchInputModelAny, AsyncSession], Awaitable[BatchInputModelAny]]
        | None
    ) = None,
    postprocessor_output: (
        Callable[[Sequence[T_DB], AsyncSession], Awaitable[Sequence[T_DB]]] | None
    ) = None,
) -> NiceAPIRoute:

    class BatchInputModel(BatchInputModel_ContainerType[int, input_model]):
        pass

    async def endpoint(
        payload: BatchInputModel,
        db: AsyncSession = Depends(get_db_session),
    ):
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)  # type: ignore

        updated_entities = await service.partial_update_multi(
            session=db, update_list=payload
        )

        if postprocessor_output:
            updated_entities = await postprocessor_output(updated_entities, db)

        return updated_entities

    route = NiceAPIRoute(
        route=APIRoute(
        path=f"{prefix}",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type: ignore
        response_model=response_model,
        endpoint=endpoint,),
        service=service
    )
    return route
