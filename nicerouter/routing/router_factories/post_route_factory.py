from collections.abc import AsyncGenerator, Awaitable, Callable 
from fastapi import Depends, HTTPException, Query, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.normalization.object_builders import build_normalized_store_object
from nicerouter.normalization.type_builder import build_normalized_store_type
from nicerouter.routing import routes_service
from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import get_db_class_fields
from nicerouter.routing.routes_service import sa_to_dict, tags_from_prefix 
from nicerouter.routing.service.service_factory import ServiceFactory
from sqlalchemy.orm import DeclarativeBase


def create_post_route[T_DB: DeclarativeBase](
    *,
    input_model: type[BaseModel],
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service_factory: ServiceFactory[T_DB, int],
    prefix: str,
    preprocessor_input: (
        Callable[[BaseModel, AsyncSession], Awaitable[BaseModel]] | None
    ) = None,
    postprocessor_output: (
        Callable[[T_DB, AsyncSession], Awaitable[T_DB]] | None
    ) = None,
) -> APIRoute:
     
    async def endpoint(
        payload: input_model, db: AsyncSession = Depends(get_db_session) # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        service = service_factory.create(db=db)
         
        updated_entity = await service.save(id=id, updates=payload)

        if postprocessor_output:
            updated_entity = await postprocessor_output(updated_entity, db)
  
        return updated_entity

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["POST"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,
    )
