from collections.abc import AsyncGenerator, Callable
from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.routing.types import NiceAPIRoute
from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import build_exclude_fields_set
from nicerouter.routing.routes_service import tags_from_prefix
from sqlalchemy.orm import DeclarativeBase
from nicerouter.routing.service.service_util import check_entity_found
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


def create_get_by_id_route[T_DB: DeclarativeBase, T_DTO: BaseModel](
    *,
    response_model: type[T_DTO],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[T_DB, T_DTO],
    prefix: str,
) -> NiceAPIRoute:

    async def endpoint(
        id: int,
        db: AsyncSession = Depends(get_db_session),  # type: ignore
        params: CommonQueryParams = Depends(),
    ):  # type: ignore  # noqa: A002

        exclude_fields: list[str] = (
            list(build_exclude_fields_set(params.exclude_fields))
            if params.exclude_fields
            else []
        )
        entity = await service.get_by_id_with_options(
            session=db,
            id=id,
            response_model=response_model,
            max_depth=params.max_depth,
            exclude_fields=exclude_fields,
        )

        entity = check_entity_found(entity)

        from nicerouter.sa_to_dict import sa_to_dict

        entity = sa_to_dict(entity)

        return entity

    route = NiceAPIRoute(
        route=APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["GET"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=response_model,
        endpoint=endpoint,),
        service=service,
    )
    return route
