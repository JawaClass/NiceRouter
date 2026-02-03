from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated 
from fastapi import Depends, HTTPException, Query, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.normalization.object_builders import build_normalized_store_object
from nicerouter.normalization.type_builder import build_normalized_store_type
from nicerouter.routing import routes_service
from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import get_db_class_fields
from nicerouter.routing.routes_service import sa_to_dict, tags_from_prefix
from nicerouter.routing.sa_select_in_deep import select_relationships_deep 
from nicerouter.routing.service.service_factory import ServiceFactory
from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.service.service_util import check_entity_found

class CommonQueryParams(BaseModel):
    response_type: ResponseType = Field(
        default=ResponseType.Nested,
        description="returns the requested entities as a normalized store object..."
    )
    exclude_fields: str | None = Field(
        default=None, 
        description="Columns to exclude from response. Separated by ;", 

    )
    max_depth: int | None = Field(
        default=3, 
        description="Specify the maximum depth relationships shall be loaded."
    )

def create_get_by_id_route[T_DB: DeclarativeBase](
    *,
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service_factory: ServiceFactory[T_DB, int],
    prefix: str,
) -> APIRoute:
     
    async def endpoint(
        id: int, db: 
        AsyncSession = Depends(get_db_session), # type: ignore
        params: CommonQueryParams = Depends(),
    ):  # type: ignore  # noqa: A002
        
        service = service_factory.create(db=db)
         
        entity = await service.get_by_id(id=id)

        entity = check_entity_found(entity)

        return entity

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["GET"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,
    )
