from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from nicerouter.routing.models import ResponseType
from nicerouter.routing.param_builders import build_exclude_fields_set
from nicerouter.routing.routes_service import tags_from_prefix
from nicerouter.routing.service.crud_service import CrudService
from nicerouter.routing.service.service_util import check_entity_found
from nicerouter.routing.service.types import EntiyType, InputType, OutputType
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


def create_get_by_id_route[Entiy: EntiyType, Input: InputType, Output: OutputType](
    *,
    mask_class: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    service: CrudService[Entiy, Input, Output, Any],
    prefix: str,
    **route_kwargs: Any,
) -> NiceAPIRoute[Entiy, Input, Output, Any]:

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
            mask_class=mask_class,
            max_depth=params.max_depth,
            exclude_fields=exclude_fields,
        )

        entity = check_entity_found(entity)

        entity_as_output = service.entity_mapper.entity2output(entity)

        return entity_as_output

    response_model = service.entity_mapper.output_cls
    route = NiceAPIRoute(
        route=APIRoute(
            path=f"{prefix}/{{id}}",
            methods=["GET"],
            tags=tags_from_prefix(prefix),  # type:ignore
            response_model=response_model,
            endpoint=endpoint,
            **route_kwargs,
        ),
        service=service,
    )
    return route
