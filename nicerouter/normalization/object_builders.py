from typing import Any, Iterable
from pydantic import BaseModel
from nicerouter.normalization.normalizer import ObjectNormalizer
  
def normalize_rows[E](
    *,
    # the pydantic model of the passed rows
    response_model: type[BaseModel],
    # the items that should be normalized
    # can be directly from fetched sql
    rows: E | Iterable[E],
): 
    if not isinstance(rows, Iterable):
        rows = [rows]

    normalizer = ObjectNormalizer()

    for row in rows:
        obj = response_model.model_validate(row)
        normalizer.normalize(obj=obj, id_name="id")
    return normalizer.store


def build_normalized_store_object[E](
    *,
    normalized_response_type: type[BaseModel],
    response_model: type[BaseModel],
    items: list[type[E]], 
):
    # normalize all the objects
    normalized = normalize_rows( 
        response_model=response_model,
        rows=items,
    ) 
    # create an emtpty pydantic object normalized_response_type
    # fields need to be required in pydantic models for nice 
    # openapi generation so we add default values manually
    empty_slices = {field: dict() for field in normalized_response_type.model_fields}
    empty_slices_store = normalized_response_type(**empty_slices)
    # return the merged empty + normalized slices
    store = {**empty_slices_store.model_dump(), **normalized}
    sorted_store = dict(sorted(store.items()))
    return sorted_store