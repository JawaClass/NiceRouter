from contextlib import asynccontextmanager
from typing import Any, Literal, Sequence

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, load_only
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.exc import IntegrityError 
from nicerouter.routing.param_builders import (
    build_exclude_fields_set,
    build_filter_by,
    build_select_fields,
    build_sort_by,
)
from nicerouter.routing.sa_select_in_deep import select_relationships_deep

OnRecursion = Literal["raise", "ignore"]


def sa_to_dict(
    obj, *, depth=None, path: dict | None = None, on_recursion: OnRecursion = "ignore"
):
    """
    Safely convert a SQLAlchemy DeclarativeBase object (or list of them)
    into plain Python dictionaries — avoiding circular references and
    unloaded relationships.
    """
    type_ = type(obj)

    # print(f"sa_to_dict: {depth=} {type(obj)}")

    if isinstance(obj, (type(None), int, float, str, bool)):
        return obj

    if depth is None:
        depth = 0

    if path is None:
        path = dict()  # dict is an ordered set

    if type_ in path:
        if on_recursion == "raise":
            path = [k.__name__ for k in path.keys()] # type: ignore
            msg = f"Circular Recursion detected @ {depth=} :: {type_=} in {path=}"
            raise ValueError(msg)
        else:
            return None

    # ORM-mapped class instance
    if isinstance(obj, DeclarativeBase):
        result = {}

        path[type_] = None

        for key, col_prop in obj.__mapper__.column_attrs.items():
            result[key] = getattr(obj, key)

        for key, rel_prop in obj.__mapper__.relationships.items():
            # only serialize if the relationship is loaded
            if key in obj.__dict__:
                result[key] = sa_to_dict(
                    getattr(obj, key),
                    depth=depth + 1,
                    path=path,
                    on_recursion=on_recursion,
                )

        path.pop(type_)

        return result

    # Handle list-like relationships
    if isinstance(obj, InstrumentedList):
        return [sa_to_dict(item, depth=depth + 1, path=path) for item in obj]

    # # Return plain value (non-SQLAlchemy type)
    # visited[obj_id] = obj
    return obj


async def scalar_or_throw_by_id(
    *,
    db: AsyncSession,
    db_class: type[Any],
    id: int,
):
    query = sa.select(db_class).where(db_class.id == id)
    return await scalar_or_throw(db=db, db_class=db_class, query=query)


async def scalar_or_throw(
    *,
    db: AsyncSession,
    db_class: type[Any],
    query: sa.Select,
):
    result = await db.execute(query)
    instance = result.scalar()
    if not instance:
        raise HTTPException(status_code=404, detail=f"{db_class.__name__} not found")
    return instance


async def get_all[E](
    db_class: type[E],
    response_model: type[BaseModel],
    db: AsyncSession,
    limit: int,
    offset: int,
    query: sa.Select | None = None,
    sort_by: str | None = None,
    filter_by: str | None = None,
    exclude_fields: str | None = None,
    max_depth: int | None = None,
):
    options = []
    exclude_fields_set: set[str] = set()

    # exclude fields from select
    if exclude_fields:
        exclude_fields_set = build_exclude_fields_set(exclude_fields)
        load_only_fields = build_select_fields(db_class, exclude_fields_set)
        if len(load_only_fields):
            options.append(load_only(*load_only_fields))

    stmt = query or sa.select(db_class).options(
        *options,
        *select_relationships_deep(
            db_class,
            response_model,
            exclude_field_names=exclude_fields_set,
            max_depth=max_depth,
        ),
    )

    # add filter
    if filter_by:
        # Get available column names on the model
        filters = build_filter_by(filter_by=filter_by, db_class=db_class)

        if filters:
            stmt = stmt.where(*filters)

    # add offset
    stmt = stmt.offset(offset=offset).limit(limit=limit)

    # add sorting
    if sort_by:
        order_columns = build_sort_by(sort_by=sort_by, db_class=db_class)
        stmt = stmt.order_by(*order_columns)

    result = await db.execute(stmt)
    instances = result.scalars().all()
    # print("get_all: instances:")
    # pprint(instances)
    return instances


async def get_by_id[E](
    id: int,
    db_class: type[E],
    response_model: type[BaseModel],
    db: AsyncSession,
    query: sa.Select | None,
    id_field: str = "id",
    exclude_fields: str | None = None,
    max_depth: int | None = None,
):
    options = []
    exclude_fields_set: set[str] = set()

    # exclude fields from select
    if exclude_fields:
        exclude_fields_set = build_exclude_fields_set(exclude_fields)
        load_only_fields = build_select_fields(db_class, exclude_fields_set)
        if len(load_only_fields):
            options.append(load_only(*load_only_fields))

    stmt = query or sa.select(db_class).options(
        *options,
        *select_relationships_deep(
            db_class,
            response_model,
            exclude_field_names=exclude_fields_set,
            max_depth=max_depth,
        ),
    )
    stmt = stmt.where(getattr(db_class, id_field) == id)
    item = await scalar_or_throw(db=db, db_class=db_class, query=stmt)
    return item


def tags_from_prefix(prefix: str) -> Sequence[str]:
    return [prefix.strip("/").split("/")[0]]


 

@asynccontextmanager
async def commit_db_ops(db: AsyncSession):
    try: 
        yield
        await db.commit()
    except HTTPException:
        # If it's already a FastAPI HTTPException (like 404), 
        # just let it fly out to the client.
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        err_msg = str(e.orig).lower()
        if "foreign key" in err_msg or "violates foreign key" in err_msg:
            detail = "Action failed: This record is still referenced by other data."
            status_code = status.HTTP_409_CONFLICT
        elif "unique" in err_msg or "already exists" in err_msg:
            detail = "Action failed: A record with this value already exists."
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            detail = "Database integrity violation."
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred."
        )