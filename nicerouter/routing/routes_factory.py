from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable
from enum import Enum
from functools import cache, partial
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import Depends, HTTPException, Query, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.routing import routes_service
from nicerouter.routing.sa_select_in_deep import select_relationships_deep
from nicerouter.routing.models import ResponseType
from nicerouter.normalization.object_builders import build_normalized_store_object
from nicerouter.normalization.type_builder import build_normalized_store_type 
from nicerouter.routing.routes_service import tags_from_prefix 


def create_get_all_route(
    *,
    db_class: type[Any],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    query: sa.Select | None = None,
    prefix: str,
) -> APIRoute:
    tags = routes_service.tags_from_prefix(prefix)
    fields_lookup = routes_service.get_db_class_fields(db_class=db_class)

    fields_filter_by_example = ",".join([f for f in fields_lookup])

    async def endpoint(
        request: Request,
        db: AsyncSession = Depends(get_db_session),
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
                description=f"Columns to filter by. Fields sperated by ;  Example: {fields_filter_by_example}",
            ),
        ] = None,
    ):
        rows = await routes_service.get_all(
            db_class=db_class,
            response_model=response_model,
            db=db,
            limit=limit,
            offset=offset,
            query=query,
            sort_by=sort_by,
            filter_by=filter_by,
        )

        if response_type == ResponseType.Normalized:
            store = build_normalized_store_object(
                normalized_response_type=normalized_response_type, 
                items=rows, # type:ignore
                response_model=response_model,
            ) 
            return store 
        
        if response_type == ResponseType.Nested:
            return [response_model.model_validate(r) for r in rows]
        
        raise ValueError(f"Unknown response_type: {response_type}")

    normalized_response_type = build_normalized_store_type(model_class=response_model)
    response_model_union = normalized_response_type | list[response_model]
    # response_model_union = list[response_model]

    return APIRoute(
        path=prefix,
        methods=["GET"],
        tags=tags,  # type:ignore
        response_model=response_model_union,  # type: ignore
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
) -> APIRoute:
    tags = routes_service.tags_from_prefix(prefix)

    async def endpoint(
        id: int,
        response_type: Annotated[
            ResponseType,
            Query(
                description="returns the requested entities as a normalized store object perfectly for redux based state management",
            ),
        ] = ResponseType.Nested,
        db: AsyncSession = Depends(get_db_session),
    ):
        stmt = query or sa.select(db_class).options(
            *select_relationships_deep(db_class, response_model),
        )
        stmt = stmt.where(db_class.id == id)
        item = await routes_service.scalar_or_throw(db=db, db_class=db_class, query=stmt)

        if response_type == ResponseType.Normalized:

            return build_normalized_store_object(
                normalized_response_type=normalized_response_type, 
                items=[item],
                response_model=response_model,
                normalizer=normalizer
            )

        return item

    normalized_response_type = build_normalized_store_type(response_model)
    response_model_union = normalized_response_type | response_model

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["GET"],
        tags=tags,  # type:ignore
        response_model=response_model_union,
        endpoint=endpoint,
    )


def create_post_route(
    *,
    db_class: type[Any],
    input_model: type[BaseModel],
    response_model: type[BaseModel],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str, 
    normalizer: ObjectNormalizer | None = None,
    preprocessor_input: (
        Callable[[BaseModel, AsyncSession], Awaitable[BaseModel]] | None
    ) = None,
) -> APIRoute:
    tags = routes_service.tags_from_prefix(prefix)

    async def endpoint(
        payload: input_model,   # type:ignore
        response_type: Annotated[
            ResponseType,
            Query(
                description="""returns the requested entities as a normalized  
                 store object perfectly for redux based state management""",
            ),
        ] = ResponseType.Nested,
        db: AsyncSession = Depends(get_db_session),
    ):  # type: ignore
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        instance = db_class(**payload.model_dump())  # type: ignore
        db.add(instance)
        await db.commit()
        await db.refresh(instance)

        id = instance.id  # noqa: A001
        stmt = sa.select(db_class).options(
            *select_relationships_deep(db_class, response_model),
        )
        stmt = stmt.where(db_class.id == id)
        item = await routes_service.scalar_or_throw(db=db, db_class=db_class, query=stmt)

        if response_type == ResponseType.Normalized:
            return build_normalized_store_object(
                normalized_response_type=normalized_response_type, 
                items=[item],
                response_model=response_model,
                normalizer=normalizer
            )

        return item

    normalized_response_type = build_normalized_store_type(response_model)
    response_model_union = normalized_response_type | response_model

    return APIRoute(
        path=f"{prefix}",
        methods=["POST"],
        tags=tags,  # type:ignore
        response_model=response_model_union,
        endpoint=endpoint,
    )


def create_patch_route(
    *,
    db_class: type[Any],
    input_model: type[BaseModel],
    response_model: type[BaseModel] | None = None,
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
    preprocessor_input: (
        Callable[[BaseModel, AsyncSession], Awaitable[BaseModel]] | None
    ) = None,
) -> APIRoute:
    async def endpoint(id: int, payload: input_model, db: AsyncSession = Depends(get_db_session)):  # type: ignore  # noqa: A002
        if preprocessor_input:
            payload = await preprocessor_input(payload, db)

        instance = await routes_service.scalar_or_throw(
            db=db,
            db_class=db_class,
            query=sa.select(db_class).where(db_class.id == id),
        )

        for key, value in payload.model_dump(exclude_unset=True).items():  # type: ignore
            setattr(instance, key, value)

        await db.commit()
        await db.refresh(instance)
        return instance

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type:ignore
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
) -> APIRoute:
    class BatchItem(BaseModel):
        id: int
        data: input_model  # type:ignore

    class BatchInputModel(BaseModel):
        items: list[BatchItem]

    async def endpoint(
        payload: BatchInputModel, db: AsyncSession = Depends(get_db_session)
    ):
        updated_instances = []

        for item in payload.items:
            instance = await routes_service.scalar_or_throw_by_id(db=db, db_class=db_class, id=item.id)
            for key, value in item.data.model_dump(exclude_unset=True).items():  # type: ignore
                setattr(instance, key, value)

            updated_instances.append(instance)

        await db.commit()
        for instance in updated_instances:
            await db.refresh(instance)

        return updated_instances

    return APIRoute(
        path=f"{prefix}/batch",
        methods=["PATCH"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=list[response_model] if response_model else None,
        endpoint=endpoint,
    )


def create_delete_route(
    *,
    db_class: type[Any],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
) -> APIRoute:
    async def endpoint(
        id: int,
        db: AsyncSession = Depends(get_db_session),
    ):
        instance = await routes_service.scalar_or_throw(
            db=db,
            db_class=db_class,
            query=sa.select(db_class).where(db_class.id == id),
        )

        await db.delete(instance)
        await db.commit()
        return {"detail": "Deleted"}

    return APIRoute(
        path=f"{prefix}/{{id}}",
        methods=["DELETE"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=dict,
        endpoint=endpoint,
    )


def create_delete_multi_route(
    *,
    db_class: type[Any],
    get_db_session: Callable[[], AsyncGenerator[AsyncSession]],
    prefix: str,
) -> APIRoute:
    async def endpoint(id_list: list[int], db: AsyncSession = Depends(get_db_session)):
        stmt = sa.select(db_class).where(db_class.id.in_(id_list))
        result = await db.execute(stmt)
        found = result.scalars().all()

        if len(found) != len(id_list):
            missing_ids = set(id_list) - {x.id for x in found}
            raise HTTPException(status_code=404, detail=f"Missing IDs: {missing_ids}")

        for item in found:
            await db.delete(item)

        await db.commit()
        return {"detail": f"Deleted {len(found)} items"}

    return APIRoute(
        path=f"{prefix}",
        methods=["DELETE"],
        tags=tags_from_prefix(prefix),  # type:ignore
        response_model=dict,
        endpoint=endpoint,
    )
