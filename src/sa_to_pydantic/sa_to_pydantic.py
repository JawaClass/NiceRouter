from pydantic import BaseModel, Field, create_model
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint
from typing import Any, ForwardRef, get_type_hints, get_origin, get_args, Callable
from sqlalchemy.orm.attributes import InstrumentedAttribute
from types import UnionType
from src.type_utils import extract_most_inner_type
from typing import ForwardRef
from typing import Union
class SaPydanticRegistryNameSpace(dict[str, type[BaseModel]]):
    pass


REGISTRY = SaPydanticRegistryNameSpace()

 


def sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
) -> type[BaseModel]:

    reg_before = set(REGISTRY.keys())

    _sa_to_pydantic(
        model=model,
        name_generator=name_generator,
        exclude_fields=exclude_fields,
        base_model=base_model,
    )

    reg_after = set(REGISTRY.keys())

    reg_difference = reg_after - reg_before

    newly_added_models: dict[str, type[BaseModel]] = {
        k: REGISTRY[k] for k in reg_difference
    }

    for created_model in newly_added_models.values():
        created_model.model_rebuild(_types_namespace=REGISTRY)

    model_name = name_generator(model.__name__)

    resolved_result_model = REGISTRY[model_name]
    return resolved_result_model


def _sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
    _traversed: set[Any] | None = None,
    _seen: set[str] | None = None,
) -> type[BaseModel] | ForwardRef:
    model_name = name_generator(model.__name__)

    if base_model:
        assert issubclass(base_model, BaseModel), f"{base_model} not a BaseModel"

    _traversed = _traversed or set([model])

    _seen = _seen or set()

    if model_name in REGISTRY:
        return REGISTRY[model_name]

    if model_name in _seen:
        # forward reference to handle circular relationships
        return ForwardRef(model_name)

    _seen.add(model_name)

    mapper = sa.inspect(model)
    relationships = mapper.relationships
    name2annotation = get_type_hints(model)

    fields: dict[str, Any] = {}

    for name, annotation in name2annotation.items():

        if exclude_fields and name in exclude_fields:
            continue

        is_relationship = name in relationships

        inside_mapped_type = get_args(annotation)[0]

        inside_mapped_type_origin = get_origin(inside_mapped_type)

        is_union_type: bool = inside_mapped_type_origin in (Union, UnionType)

        if not is_relationship:
            field_config = ...
            if is_union_type:
                union_childs = get_args(inside_mapped_type)
                is_optional = type(None) in union_childs
                if is_optional:
                    field_config = Field(default=None)

            fields[name] = (
                inside_mapped_type,
                field_config,
            )
        else:

            sa_rel_model = extract_most_inner_type(annotation) 

            if sa_rel_model in _traversed:
                annotation_type = REGISTRY[name_generator(sa_rel_model.__name__)]
            else:
                annotation_type = _sa_to_pydantic(
                model=sa_rel_model,
                name_generator=name_generator,
                exclude_fields=None,
                _traversed=_traversed,
                _seen=_seen,
            )
            _traversed.add(sa_rel_model)

            if is_union_type:
                union_childs = get_args(inside_mapped_type)

                is_optional = type(None) in union_childs

                union_childs_replaced_sa = [
                    annotation_type if typ is sa_rel_model else typ
                    for typ in union_childs
                ]
                union_type = Union[tuple(union_childs_replaced_sa)]

                if is_optional:
                    fields[name] = (
                        union_type,
                        Field(default=None),
                    )
                else:
                    fields[name] = (union_type, ...)
            elif inside_mapped_type_origin is list:
                fields[name] = list[annotation_type]
            elif inside_mapped_type_origin is None:
                fields[name] = annotation_type
            else:
                raise ValueError(
                    f"Unresolved type inside Mapped {inside_mapped_type=} {inside_mapped_type_origin=}"
                )

    NewModel: type[BaseModel] = create_model(
        model_name,
        **fields,
        __base__=base_model or BaseModel,
        __config__={"from_attributes": True},
        __module__="dynamic",
    )
    REGISTRY[model_name] = NewModel

    assert model_name in REGISTRY

    return NewModel
 

if __name__ == "__main__":

    class Base(DeclarativeBase):
        pass
    class B(Base):
        __tablename__ = "b"
        id: Mapped[int] = mapped_column(primary_key=True)
        a_id: Mapped[int] = mapped_column(sa.ForeignKey("A.id"))

    class A(Base):
        __tablename__ = "A"
        id: Mapped[int] = mapped_column(primary_key=True)
        foo: Mapped[str]
        bar: Mapped[int]
        optional: Mapped[int | None]

        b: Mapped[B | None] = relationship()
        b2: Mapped[B] = relationship()

    model = sa_to_pydantic(model=A, name_generator=lambda x : x)
    
    print("pydantic_model", model)
    pprint(model.model_fields)

    assert model.model_fields["foo"].is_required()
    assert model.model_fields["bar"].is_required()
    assert model.model_fields["id"].is_required()
    assert not model.model_fields["optional"].is_required()
    assert not model.model_fields["b"].is_required()
    assert model.model_fields["b2"].is_required()

    model.model_validate(A(id=1, foo="foo", bar=5, b2=B(id=1, a_id=999)))
