from typing import Sequence, Union, get_origin
from pydantic import BaseModel
from nicerouter.type_utils import extract_most_inner_type 

def is_reference_type(typ: type) -> bool:
    if typ is None:
        return False

    inner_type = extract_most_inner_type(typ)
    container_type = get_origin(typ)  # type: ignore

    if inner_type is None:
        return False

    # Check if inner_type is a subclass of BaseModel
    # and either container_type is not a Sequence or container_type is None
    # print(f"issubclass.... {inner_type=}, {container_type=} {container_type is Union}")
    if issubclass(inner_type, BaseModel):
        if container_type is None:
            return True
        if container_type is Union:
            return True
        if not issubclass(container_type, Sequence):
            return True
    return False

def is_list_reference_type(typ: type) -> bool:
    container_type = get_origin(typ)  # type: ignore
    if container_type is None:
        return False
    if container_type is Union:
            return False
    if not issubclass(container_type, Sequence):
        return False
    inner_type = extract_most_inner_type(typ)
    return is_reference_type(inner_type)