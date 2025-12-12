from typing import Iterable

from pydantic import BaseModel

from nicerouter.normalization.normalizer import ObjectNormalizer


def normalize_rows[E](
    *,
    normalizer: ObjectNormalizer,
    # the pydantic model of the passed rows
    response_model: type[BaseModel],
    # the items that should be normalized
    # can be directly from fetched sql
    rows: E | Iterable[E],
):
    if not isinstance(rows, Iterable):
        rows = [rows]

    for row in rows:
        normalizer.normalize(obj=row, obj_model=response_model, id_name="id")
    return normalizer.store


def build_normalized_store_object[E](
    *,
    normalized_response_type: type[BaseModel],
    response_model: type[BaseModel],
    items: list[type[E]],
    normalizer: ObjectNormalizer | None = None,
):
    normalizer = normalizer or ObjectNormalizer()
    # normalize all the objects
    normalized = normalize_rows(
        normalizer=normalizer,
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
