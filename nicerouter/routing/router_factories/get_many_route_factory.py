from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import build_exclude_fields_set, build_filter_by
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_base_service import GetManyParams
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputManyType,
    OutputType,
)
from nicerouter.routing.types import NiceAPIRoute


class CommonQueryParams(BaseModel):
    response_type: ResponseType = Field(
        default=ResponseType.Nested,
        description="returns the requested entities as a normalized store object...",
    )
    exclude_fields: str | None = Field(
        default=None,
        description="Columns to exclude from response. Separated by ;",
    )
    max_depth: int = Field(
        default=3,
        description="Specify the maximum depth relationships shall be loaded.",
    )
    limit: int = Field(
        default=10,
        description="Max length.",
    )
    offset: int = Field(
        default=0,
        description="Start return entities from offset.",
    )
    filter_by: str | None = Field(
        default=None, description="Columns to filter by. Fields sperated by ;"
    )


def create_get_multi_route[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
](
    *,
    mask_class: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, OutputMany],
    prefix: str,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, OutputMany]:

    async def endpoint(
        db: AsyncSession = Depends(get_db_session),
        params: CommonQueryParams = Depends(),
    ):

        exclude_fields: list[str] = (
            list(build_exclude_fields_set(params.exclude_fields))
            if params.exclude_fields
            else []
        )

        db_class = service.repository.model_cls

        where_clause = (
            build_filter_by(filter_by=params.filter_by, db_class=db_class)
            if params.filter_by
            else []
        )

        get_many_params: GetManyParams = {
            "max_depth": params.max_depth,
            "exclude_fields": exclude_fields,
            "mask_class": mask_class,
            "limit": params.limit,
            "offset": params.offset,
            "where_clause": where_clause,
        }

        entities = await service.get_many(session=db, params=get_many_params)
        entities_list = list(entities)

        entites_as_output = service.entity_mapper.entities2output(entities_list)

        return entites_as_output

    response_model = service.entity_mapper.output_many_cls

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}",
            methods=["GET"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=response_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )
    return route
