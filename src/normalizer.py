

from typing import Any, Iterable
from pydantic import BaseModel


@cache
def name_strategy(model_type: type[BaseModel], *args):
    print("name_strategy ::", model_type.__name__)
    strategy = partial(
        class_name_strategy,
        prefixes=("Go",),
        suffixes=("OutSchema",),
        case_strategy="Snake",
    )
    return strategy(model_type=model_type)


# src.endpoints.articles_manufacturer.schema.GoArticleManufacturerOutSchema
@cache
def build_normalize_response_type(model_class: type[BaseModel]):
    print("#\n#\n#\n")
    print("build_normalize_response_type............................")

    rv = build_normalized_response_model(
        model_class=model_class,
        name_strategy=name_strategy,
    )
    print("   rv .. ----->")
    print(rv.__name__)
    from pprint import pprint

    pprint(rv.model_fields)
    # input("...")
    return rv






def normalize_response[E](
    *,
    entity_name: str,
    response_model: type[BaseModel],
    rows: E | Iterable[E],
):
    normalizer = Normalizer(canonical_name_strategy=name_strategy)

    entity_name = name_strategy(model_type=response_model)

    if not isinstance(rows, Iterable):
        rows = [rows]

    for row in rows:
        # print("validate:", row)
        obj = response_model.model_validate(row)
        normalizer.normalize(name=entity_name, obj=obj, id_name="id")
    # print("normalizer.store.keys", normalizer.store.keys())
    return normalizer.store


def build_normalize_response(
    *,
    normalized_response_type: type[BaseModel],
    response_model: type[BaseModel],
    items: list[type[Any]],
    entity_name: str,
):
    normalized = normalize_response(
        entity_name=entity_name,
        response_model=response_model,
        rows=items,
    )

    # fields need to be required in pydantic models for nice openapi generation so we add default values manually
    empty_slices = {field: dict() for field in normalized_response_type.model_fields}
    empty_slices_store = normalized_response_type(**empty_slices)

    return {**empty_slices_store.model_dump(), **normalized}

