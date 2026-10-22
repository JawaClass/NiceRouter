from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import Depends, Query, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.normalization.type_builder import build_normalized_store_model
from nicerouter.routing.models.models import (
    DeleteBatchEntityResponse,
    DeleteEntityResponse,
    ResponseType,
    create_batch_input_model,
)
from nicerouter.routing.routes.routes_helper import tags_from_prefix
from nicerouter.routing.service import service_methods
from nicerouter.routing.service.param_builders import get_db_class_fields

type PreProcessor[E: BaseModel] = Callable[[E, AsyncSession], Awaitable[E]]
type PostProcessor[E: object] = Callable[[E, AsyncSession], Awaitable[E]]
type ServiceMethod = Callable[..., Awaitable[Any]]


def create_get_all_route[E: DeclarativeBase](
    *,
    db_class: type[E],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    query: sa.Select | None = None,
    prefix: str,
    normalizer: ObjectNormalizer | None = None,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    tags = tags_from_prefix(prefix)
    fields_lookup = get_db_class_fields(db_class=db_class)
    available_fields = ",".join([f for f in fields_lookup])

    async def endpoint(
        request: Request,
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
        limit: Annotated[int, Query(ge=1, le=50_000)] = 50_000,
        offset: Annotated[int, Query(ge=0)] = 0,
        response_type: Annotated[
            ResponseType,
            Query(
                description="returns the requested entities as a normalized store object perfectly for redux based state management",
            ),
        ] = ResponseType.Nested,
        sort_by: Annotated[
            str | None,
            Query(
                description="Columns to sort by sperated by , Prefix with '-' for descending. Example: name,-created_at",
            ),
        ] = None,
        filter_by: Annotated[
            str | None,
            Query(
                description=f"Columns to filter by. Fields sperated by ;  Example: {available_fields}",
            ),
        ] = None,
        exclude_fields: Annotated[
            str | None,
            Query(
                description=f"Columns to exclude from response. Fields sperated by ;  Example: {available_fields}",
            ),
        ] = None,
        max_depth: Annotated[
            int | None,
            Query(
                description="Specify the maximum depth relationships shall be loaded. Defaults to 3.",
            ),
        ] = 3,
    ):
        if preprocessor:
            await preprocessor(request, db)

        response = await (service_method or service_methods.get_all)(
            db_class=db_class,
            response_model=response_model,
            response_type=response_type,
            normalized_response_model=normalized_response_type,
            db=db,
            limit=limit,
            offset=offset,
            query=query,
            sort_by=sort_by,
            filter_by=filter_by,
            exclude_fields=exclude_fields,
            max_depth=max_depth,
            normalizer=normalizer,
        )

        if postprocessor:
            response = await postprocessor(response, db)

        return response

    normalized_response_type = build_normalized_store_model(model_class=response_model)

    response_type_list = list[response_model]  # ty: ignore[invalid-type-form]
    response_model_union = normalized_response_type | response_type_list

    return APIRoute(
        path=prefix,
        methods=["GET"],
        tags=[*tags],
        response_model=response_model_union,
        endpoint=endpoint,
    )


def create_get_by_id_route(
    *,
    db_class: type[Any],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    query: sa.Select | None,
    prefix: str,
    normalizer: ObjectNormalizer | None = None,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    tags = tags_from_prefix(prefix)
    fields_lookup = get_db_class_fields(db_class=db_class)
    available_fields = ",".join([f for f in fields_lookup])

    async def endpoint(
        id: int,
        response_type: Annotated[
            ResponseType,
            Query(
                description="returns the requested entities as a normalized store object perfectly for redux based state management",
            ),
        ] = ResponseType.Nested,
        exclude_fields: Annotated[
            str | None,
            Query(
                description=f"Columns to exclude from response. Fields sperated by ;  Example: {available_fields}",
            ),
        ] = None,
        max_depth: Annotated[
            int | None,
            Query(
                description="Specify the maximum depth relationships shall be loaded. Defaults to 3.",
            ),
        ] = 3,
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
    ):
        if preprocessor:
            await preprocessor(id, db)

        response = await (service_method or service_methods.get_by_id)(
            item_id=id,
            db_class=db_class,
            response_model=response_model,
            db=db,
            query=query,
            exclude_fields=exclude_fields,
            max_depth=max_depth,
            response_type=response_type,
            normalized_response_model=normalized_response_model,
            normalizer=normalizer,
        )

        if postprocessor:
            response = await postprocessor(response, db)

        return response

    normalized_response_model = build_normalized_store_model(response_model)
    response_model_union = normalized_response_model | response_model

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["GET"],
        tags=[*tags],
        response_model=response_model_union,
        endpoint=endpoint,
    )


def create_post_route[E: DeclarativeBase](
    *,
    db_class: type[E],
    input_model: type[BaseModel],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    normalizer: ObjectNormalizer | None = None,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    tags = tags_from_prefix(prefix)

    async def endpoint(
        payload: input_model,  # ty: ignore[invalid-type-form]
        response_type: Annotated[
            ResponseType,
            Query(
                description="""returns the requested entities as a normalized  
                 store object perfectly for redux based state management""",
            ),
        ] = ResponseType.Nested,
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
    ):
        if preprocessor:
            payload = await preprocessor(payload, db)

        response = await (service_method or service_methods.post)(
            db_class=db_class,
            response_model=response_model,
            normalized_response_model=normalized_response_type,
            db=db,
            payload=payload,
            normalizer=normalizer,
            response_type=response_type,
        )

        if postprocessor:
            response = await postprocessor(response, db)

        return response

    normalized_response_type = build_normalized_store_model(response_model)
    response_model_union = normalized_response_type | response_model

    return APIRoute(
        path=f"{prefix}",
        methods=["POST"],
        tags=tags,  # type: ignore
        response_model=response_model_union,
        endpoint=endpoint,
    )


def create_patch_route[E: DeclarativeBase, I: BaseModel](
    *,
    db_class: type[E],
    input_model: type[I],
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    preprocessor: PreProcessor[I] | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    async def endpoint(
        id: int,
        payload: input_model,  # ty: ignore[invalid-type-form]
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
    ):
        if preprocessor:
            payload = await preprocessor(payload, db)

        updated_instance = await (service_method or service_methods.patch)(
            item_id=id, db=db, db_class=db_class, payload=payload
        )

        if postprocessor:
            updated_instance = await postprocessor(updated_instance, db)

        return updated_instance

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["PATCH"],
        tags=[*tags_from_prefix(prefix)],
        response_model=response_model,
        endpoint=endpoint,
    )


def create_batch_patch_route_varied(
    *,
    db_class: type[Any],
    input_model: type[BaseModel],
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    name = db_class.__name__

    batch_input_model = create_batch_input_model(input_model=input_model, name=name)

    async def endpoint(
        payload: batch_input_model,  # ty: ignore[invalid-type-form]
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
    ):
        if preprocessor:
            payload = await preprocessor(payload, db)

        response = await (service_method or service_methods.patch_batch)(
            db=db, db_class=db_class, payload=payload
        )

        if postprocessor:
            response = await postprocessor(response, db)

        return response

    return APIRoute(
        path=f"{prefix}/batch",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type: ignore
        response_model=list[response_model] if response_model else None,
        endpoint=endpoint,
    )


def create_delete_route(
    *,
    db_class: type[Any],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    async def endpoint(
        id: int,
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
    ):
        if preprocessor:
            await preprocessor(id, db)

        result = await (service_method or service_methods.delete)(
            entity_id=id, db=db, db_class=db_class
        )

        if postprocessor:
            await postprocessor(result, db)

        return result

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["DELETE"],
        tags=[*tags_from_prefix(prefix)],
        response_model=DeleteEntityResponse,
        endpoint=endpoint,
    )


def create_delete_multi_route(
    *,
    db_class: type[Any],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    preprocessor: PreProcessor | None = None,
    postprocessor: PostProcessor | None = None,
    service_method: ServiceMethod | None = None,
) -> APIRoute:
    async def endpoint(id_list: list[int], db: AsyncSession = Depends(get_db_session)):  # noqa: B008
        if preprocessor:
            await preprocessor(id_list, db)

        response = await (service_method or service_methods.delete_batch)(
            id_list=id_list, db=db, db_class=db_class
        )

        if postprocessor:
            response = await postprocessor(response, db)

        return response

    return APIRoute(
        path=f"{prefix}",
        methods=["DELETE"],
        tags=[*tags_from_prefix(prefix)],
        response_model=DeleteBatchEntityResponse,
        endpoint=endpoint,
    )
