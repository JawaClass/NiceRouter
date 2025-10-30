from typing import Any, Literal

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel, create_model, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import DeclarativeBase, load_only
from nicerouter.routing.sa_select_in_deep import select_relationships_deep
from pprint import pprint

from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import DeclarativeBase


from sqlalchemy.orm.attributes import instance_state


def sa_to_dict(obj, visited=None):
    """
    Safely convert a SQLAlchemy DeclarativeBase object (or list of them)
    into plain Python dictionaries — avoiding circular references and
    unloaded relationships.
    """

    if isinstance(obj, (type(None), int, float, str, bool)):
        return obj

    if visited is None:
        visited = dict()

    # Avoid recursion loops on circular references
    obj_id = id(obj)
    if obj_id in visited:
        return visited[obj_id]

    # ORM-mapped class instance
    if isinstance(obj, DeclarativeBase):
        result = {}

        for key, col_prop in obj.__mapper__.column_attrs.items():
            result[key] = getattr(obj, key)

        for key, rel_prop in obj.__mapper__.relationships.items():
            # only serialize if the relationship is loaded
            if key in obj.__dict__:
                result[key] = sa_to_dict(getattr(obj, key), visited)

        return result

    # Handle list-like relationships
    if isinstance(obj, InstrumentedList):
        return [sa_to_dict(item, visited) for item in obj]

    # Return plain value (non-SQLAlchemy type)
    visited[obj_id] = obj
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


def is_column_field(db_class: object, field: str):
    attr = getattr(db_class, field)
    if not attr:
        return False

    return isinstance(attr, InstrumentedAttribute)


def build_filter_by(filter_by: str, db_class: object):
    filter_expresssions = filter_by.split(",")
    filters = []
    for filter_expr in filter_expresssions:
        field, value = filter_expr.split("=")
        if not is_column_field(db_class, field):
            raise HTTPException(
                status_code=400, detail=f"Invalid filter field: {field}"
            )
        filters.append(getattr(db_class, field) == value)
    return filters


def build_sort_by(sort_by: str, db_class: object):
    order_columns = []
    fields = sort_by.split(",")
    for field in fields:
        desc = False
        if field.startswith("-"):
            desc = True
            field = field[1:]
        if not is_column_field(db_class, field):
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {field}")
        col = getattr(db_class, field)
        order_columns.append(col.desc() if desc else col.asc())
    return order_columns


def get_db_class_fields(db_class: object):
    valid_attrs: dict[str, InstrumentedAttribute] = {
        attr: getattr(db_class, attr)
        for attr in dir(db_class)
        if isinstance(getattr(db_class, attr), InstrumentedAttribute)
    }
    return valid_attrs


def build_select_fields(db_class: object, exclude_fields_set: set[str]):
    db_class_fields = get_db_class_fields(db_class)
    load_only_fields = [
        field
        for name, field in db_class_fields.items()
        if name not in exclude_fields_set and not field.property._is_relationship
    ]
    return load_only_fields


def build_exclude_fields_set(exclude_fields: str):
    exclude_fields_list = (exclude_fields).replace(" ", "").split(",")
    exclude_fields_set = set(exclude_fields_list)
    return exclude_fields_set


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
):
    options = []
    exclude_fields_set = set()

    # exclude fields from select
    if exclude_fields:
        exclude_fields_set = build_exclude_fields_set(exclude_fields)
        load_only_fields = build_select_fields(db_class, exclude_fields_set)
        if len(load_only_fields):
            options.append(load_only(*load_only_fields))

    stmt = query or sa.select(db_class).options(
        *options,
        *select_relationships_deep(
            db_class, response_model, exclude_field_names=exclude_fields_set
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
):

    options = []
    exclude_fields_set = set()

    # exclude fields from select
    if exclude_fields:
        exclude_fields_set = build_exclude_fields_set(exclude_fields)
        load_only_fields = build_select_fields(db_class, exclude_fields_set)
        if len(load_only_fields):
            options.append(load_only(*load_only_fields))

    stmt = query or sa.select(db_class).options(
        *options,
        *select_relationships_deep(
            db_class, response_model, exclude_field_names=exclude_fields_set
        ),
    )
    stmt = stmt.where(getattr(db_class, id_field) == id)
    item = await scalar_or_throw(db=db, db_class=db_class, query=stmt)
    return item


def tags_from_prefix(prefix: str):
    return [prefix.strip("/").split("/")[0]]
