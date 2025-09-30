from typing import Sequence
from pydantic import BaseModel
from src.type_utils import extract_most_inner_type
from typing import get_origin

def is_reference_type(typ: type) -> bool:
    if typ is None:
        return False

    inner_type = extract_most_inner_type(typ)
    container_type = get_origin(typ)  # type: ignore

    if inner_type is None:
        return False

    # Check if inner_type is a subclass of BaseModel
    # and either container_type is not a Sequence or container_type is None
    if issubclass(inner_type, BaseModel):
        if container_type is None or not issubclass(container_type, Sequence):
            return True
    return False

def is_list_reference_type(typ: type) -> bool:
    container_type = get_origin(typ)  # type: ignore
    if container_type is None or not issubclass(container_type, Sequence):
        return False

    inner_type = extract_most_inner_type(typ)
    return is_reference_type(inner_type)