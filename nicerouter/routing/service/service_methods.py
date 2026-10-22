from typing import Sequence, Any
import sqlalchemy as sa
from nicerouter.routing.exceptions import NotFoundError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from nicerouter.normalization.normalizer import ObjectNormalizer
from nicerouter.normalization.object_builders import build_normalized_store_object
from nicerouter.routing.models.models import (
    BatchInputModelProtocol,
    DeleteBatchEntityResponse,
    DeleteEntityResponse,
    ResponseType,
)
from nicerouter.routing.service import db_helper, service_helper
from nicerouter.routing.service.sa_select_in_deep import select_relationships_deep
from nicerouter.routing.service.service_helper import id_column, id_of, sa_to_dict


async def post[E: DeclarativeBase](
    db_class: type[E],
    response_model: type[BaseModel],
    normalized_response_model: type[BaseModel],
    db: AsyncSession,
    response_type: ResponseType,
    payload: Any,
    normalizer: ObjectNormalizer | None = None,
):
    async with db_helper.commit_db_ops(db=db):
        instance = db_class(**payload.model_dump())
        db.add(instance)

    await db.refresh(instance)

    id = id_of(instance)
    stmt = sa.select(db_class).options(
        *select_relationships_deep(db_class, response_model),
    )
    stmt = stmt.where(id_column(db_class) == id)
    item = await service_helper.scalar_or_throw(db=db, db_class=db_class, query=stmt)

    if response_type == ResponseType.Nested:
        return item

    elif response_type == ResponseType.Normalized:
        return build_normalized_store_object(
            normalized_response_type=normalized_response_model,
            items=[item],
            response_model=response_model,
            normalizer=normalizer,
        )


async def patch[E: DeclarativeBase](
    item_id: int, db: AsyncSession, db_class: type[E], payload: BaseModel
):
    async with db_helper.commit_db_ops(db=db):
        instance = await service_helper.scalar_or_throw(
            db=db,
            db_class=db_class,
            query=sa.select(db_class).where(id_column(db_class) == item_id),
        )

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)

    await db.refresh(instance)
    return instance


async def patch_batch[E: DeclarativeBase](
    db: AsyncSession, db_class: type[E], payload: BatchInputModelProtocol
) -> list[E]:
    updated_instances: list[E] = []

    async with db_helper.commit_db_ops(db=db):
        for item in payload.items:
            instance = await service_helper.scalar_or_throw_by_id(
                db=db, db_class=db_class, id=item.id
            )
            for key, value in item.data.model_dump(exclude_unset=True).items():
                setattr(instance, key, value)

            updated_instances.append(instance)

    for instance in updated_instances:
        await db.refresh(instance)

    return updated_instances


async def get_by_id[E: DeclarativeBase](
    item_id: int,
    db: AsyncSession,
    db_class: type[E],
    response_type: ResponseType,
    response_model: type[BaseModel],
    normalized_response_model: type[BaseModel],
    query: sa.Select | None,
    max_depth: int | None = None,
    exclude_fields: str | None = None,
    normalizer: ObjectNormalizer | None = None,
):
    item = await service_helper.get_by_id(
        id=item_id,
        db_class=db_class,
        response_model=response_model,
        db=db,
        query=query,
        exclude_fields=exclude_fields,
        max_depth=max_depth,
    )

    db.expunge_all()

    if response_type == ResponseType.Normalized:
        return build_normalized_store_object(
            normalized_response_type=normalized_response_model,
            items=[item],
            response_model=response_model,
            normalizer=normalizer,
        )

    if response_type == ResponseType.Nested:
        dict_item = sa_to_dict(item)
        validated_item = response_model.model_validate(dict_item)
        return validated_item


async def get_all[E: DeclarativeBase](
    db: AsyncSession,
    db_class: type[E],
    response_type: ResponseType,
    response_model: type[BaseModel],
    normalized_response_model: type[BaseModel],
    query: sa.Select | None,
    max_depth: int | None = None,
    exclude_fields: str | None = None,
    normalizer: ObjectNormalizer | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_by: str | None = None,
    filter_by: str | None = None,
):
    rows = await service_helper.get_all(
        db_class=db_class,
        db=db,
        response_model=response_model,
        limit=limit,
        offset=offset,
        query=query,
        sort_by=sort_by,
        filter_by=filter_by,
        exclude_fields=exclude_fields,
        max_depth=max_depth,
    )

    if response_type == ResponseType.Normalized:
        # Remove link to db session after fetched
        # to avoid trigger lazy loads raise runtime error
        db.expunge_all()

        store = build_normalized_store_object(
            normalized_response_type=normalized_response_model,
            items=rows,
            response_model=response_model,
            normalizer=normalizer,
        )
        return store

    if response_type == ResponseType.Nested:
        # only pass an dictionary,
        # otherwise pydantic will lazy load fields not loaded and crash async context
        validated_rows = [
            # response_model.model_validate(sa_to_dict(r)) for r in rows
            sa_to_dict(r)
            for r in rows
        ]
        return validated_rows


async def delete[E: DeclarativeBase](
    entity_id: int,
    db: AsyncSession,
    db_class: type[E],
) -> DeleteEntityResponse:
    instance = await service_helper.scalar_or_throw(
        db=db,
        db_class=db_class,
        query=sa.select(db_class).where(id_column(db_class) == entity_id),
    )
    async with db_helper.commit_db_ops(db=db):
        await db.delete(instance)

    return DeleteEntityResponse(deleted_id=entity_id)


async def delete_batch[E: DeclarativeBase](
    id_list: Sequence[int],
    db: AsyncSession,
    db_class: type[E],
) -> DeleteBatchEntityResponse:
    stmt = sa.select(db_class).where(id_column(db_class).in_(id_list))
    result = await db.execute(stmt)
    found = result.scalars().all()

    if len(found) != len(id_list):
        missing_ids = set(id_list) - {id_of(x) for x in found}
        raise NotFoundError(f"Missing IDs: {missing_ids}")

    async with db_helper.commit_db_ops(db=db):
        for item in found:
            await db.delete(item)

    return DeleteBatchEntityResponse(deleted_count=len(found))
