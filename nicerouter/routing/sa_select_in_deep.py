from collections.abc import Callable
 
from typing import Any, ForwardRef, Iterable, Sequence, get_args

import sqlalchemy as sa
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from sqlalchemy.orm import Load, selectinload

from nicerouter.type_utils import extract_most_inner_type


def select_relationships_deep(
    db_class: type[Any],
    mask_class: type[BaseModel],
    sa_load_method: Callable[[Any], Load] = selectinload,  # type:ignore
    max_depth: int = 10,
    depth: int = 0,
    exclude_field_names: Iterable[str] | None = None
) -> list[Load]:
    """Creates a hierarchy of selectinload statements for a SQLAlchemy ORM class,
    filtered by a Pydantic response model.
    """
    # print("select_relationships_deep....", db_class, mask_class)
    if depth >= max_depth:
        return []
    # Inspect relationships of the SQLAlchemy class
    mapper = sa.inspect(db_class, raiseerr=True)
    relationships = mapper.relationships

    # Get Pydantic model field info
    mask_struct: dict[str, FieldInfo] = mask_class.model_fields

    loads: list[Load] = [] 
    exclude_fields_set = set(exclude_field_names or [])
    for field_name, field_info in mask_struct.items():
        if field_name not in relationships:
            continue
        
        if field_name in exclude_fields_set:
            continue

        query = sa_load_method(getattr(db_class, field_name))
        rel = relationships[field_name]
        rel_class = rel.mapper.class_

        # Resolve the Pydantic model type for the related field
        annotation = field_info.annotation
        if annotation is None:
            continue

        child_model = extract_most_inner_type(annotation)
 
        # Recurse
        if isinstance(child_model, type) and issubclass(child_model, BaseModel):
            exclude_fields_set_next_level = {".".join(x.split(".")[1:]) 
                                             for x in exclude_fields_set 
                                             if x.startswith(f"{field_name}.")}
            
            child_loads = select_relationships_deep(
                rel_class,
                child_model,
                sa_load_method,
                depth=depth + 1,
                max_depth=max_depth,
                exclude_field_names=exclude_fields_set_next_level
            )
            query = query.options(*child_loads)

        loads.append(query)

    return loads
