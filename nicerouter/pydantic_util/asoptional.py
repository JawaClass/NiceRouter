from __future__ import annotations

from typing import Any, get_origin

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from nicerouter.type_utils import extract_most_inner_type

# class Tire(BaseModel):
#     id: int
#     brand: str
#     dim: float


# class Person(BaseModel):
#     id: int
#     name: str


# class Car(BaseModel):
#     id: int
#     name: str
#     tires: list[Tire]
#     owner: Person
#     strings: list[str]
#     optional_int: int | None


def is_a_pydantic(type_: type[Any]):
    # try:
    return issubclass(type_, BaseModel)
    # except TypeError as e:
    #     print("-------------------------> is_a_pydantic ERROR", e)
    #     input("...")
    #     return False


def new_field_info(field_original: FieldInfo):
    f_dict = field_original.asdict()

    field = FieldInfo.from_annotation(
        annotation=field_original.annotation,
    )

    for attr, value in f_dict["attributes"].items():
        setattr(field, attr, value)

    field.metadata = f_dict["metadata"].copy()

    return field


def new_field_info_as_optional(field_original: FieldInfo):
    field = new_field_info(field_original)

    type_ = field.annotation
    type_ = extract_most_inner_type(type_)
    is_pydantic = is_a_pydantic(type_)

    if is_pydantic:
        new_annotation = make_pydantic_model_optional(type_)

        # if was list, add list back
        # list get default: []
        # others get default: None
        if get_origin(field.annotation) is list:
            new_annotation = list[new_annotation]
            field.default = []
        else:
            field.annotation = new_annotation | None
            field.default = None

        return field

    return field


def make_pydantic_model_optional(model: type[BaseModel]) -> type[BaseModel]:
    field_definitions: dict[str, tuple[type[Any] | None, FieldInfo]] = {}

    for field_name, field_info in model.model_fields.items():
        new_field_info = new_field_info_as_optional(field_info)
        field_definitions[field_name] = (new_field_info.annotation, new_field_info)

    name = f"{model.__name__}_Optional"
    new_model: type[BaseModel] = create_model(name, **field_definitions)

    return new_model
