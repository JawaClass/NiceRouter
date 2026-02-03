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
from typing import Any, Sequence
from nicerouter.routing.service.model_types import BatchInputModel_ContainerType, BatchItem_ContainerType

type BatchInputModelAny = BatchInputModel_ContainerType[int, Any]

def create_patch_multi_route[T_DB: DeclarativeBase](
    *,
    input_model: type[BaseModel],
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service_factory: ServiceFactory[T_DB, int],
    prefix: str,
    preprocessor_input: (
        Callable[[BatchInputModelAny, AsyncSession], Awaitable[BatchInputModelAny]] | None
    ) = None,
    postprocessor_output: (
        Callable[[Sequence[T_DB], AsyncSession], Awaitable[Sequence[T_DB]]] | None
    ) = None,
) -> APIRoute:
    
    class BatchInputModel(BatchInputModel_ContainerType[int, input_model]):
        pass
     
    async def endpoint(
        payload: BatchInputModel, db: AsyncSession = Depends(get_db_session) # type: ignore
    ):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db) # type: ignore
            
        service = service_factory.create(db=db)
         
        updated_entities = await service.partial_update_multi(update_list=payload)

        if postprocessor_output:
            updated_entities = await postprocessor_output(updated_entities, db)
  
        return updated_entities

    return APIRoute(
        path=f"{prefix}",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,
    )
