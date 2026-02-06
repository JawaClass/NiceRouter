from collections.abc import AsyncGenerator, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import build_exclude_fields_set, build_filter_by
from nicerouter.routing.routes_service import tags_from_prefix
from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.service.crud_base_service import GetManyParams
from nicerouter.routing.service.crud_service import CrudService


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


def create_get_multi_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    response_model: type[T_DTO],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
) -> NiceAPIRoute:

    async def endpoint(
        db: AsyncSession = Depends(get_db_session),  # type: ignore
        params: CommonQueryParams = Depends(),
    ):  # type: ignore  # noqa: A002

        # exclude_fields: list[str] = (
        #     list(build_exclude_fields_set(params.exclude_fields))
        #     if params.exclude_fields
        #     else []
        # )

        db_class = service.repository.model_cls
        get_many_params: GetManyParams = {
            "limit": params.limit,
            "offset": params.offset,
            "where_clause": build_filter_by(
                filter_by=params.filter_by or "", db_class=db_class
            ),
        }

        entities = await service.get_many(session=db, params=get_many_params)

        return entities

    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}",
            methods=["GET"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=response_model,
            endpoint=endpoint,
        ),
        service=service,
    )
    return route
