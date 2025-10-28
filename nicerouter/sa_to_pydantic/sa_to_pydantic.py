from collections import defaultdict
from pydantic import BaseModel, Field, create_model
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint
from typing import (
    Any,
    ForwardRef,
    Literal,
    get_type_hints,
    get_origin,
    get_args,
    Callable,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute
from types import UnionType
from nicerouter.type_utils import extract_most_inner_type
from typing import ForwardRef
from typing import Union

CircularDepencyStrategy = Literal["raise", "forwardref", "discard"]


class PydanticRegistryEntry(BaseModel):
    name: str
    model: type[BaseModel]
    sa_model: type[DeclarativeBase]
    parent_sa_model: type[DeclarativeBase] | None = None
    namespace: str


class SaPydanticRegistryNameSpace(
    # {namespace to {pydantic_model_name to entry}}
    defaultdict[str, dict[str, PydanticRegistryEntry]]
):
    def __init__(self):
        super().__init__(dict)  # list is the default factory

    def query_model(
        self, namespace: str, model_name: str, _raise: bool = False
    ) -> PydanticRegistryEntry | None:
        models = self.get(namespace)
        if not models:
            if not _raise:
                return None
            raise KeyError(
                f"Pydantic model not found. Namespace does not exist. {namespace=}"
            )
        model = models.get(model_name)
        if not model:
            if not _raise:
                return None
            raise KeyError(
                f"Pydantic model not found. Model {model_name=} does not exist in namespace {namespace}."
            )
        return model

    def get_by_name(self, name: str, _raise: bool = False):
        for namespace in self.keys():
            for model_name in self[namespace].keys():
                if model_name == name:
                    return self[namespace][model_name]
        if _raise:
            raise KeyError(f"Model named {name} not in Registry")
        return None


REGISTRY = SaPydanticRegistryNameSpace()


def sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
    circular_depency_strategy: CircularDepencyStrategy = "discard",
    allow_optional: Callable[[type[DeclarativeBase], str], bool] | None = None,
) -> type[BaseModel]:
    """_summary_

    Args:
        model (type[DeclarativeBase]): _description_
        name_generator (Callable[[str], str]): _description_
        exclude_fields (list[str] | None, optional): _description_. Defaults to None.
        base_model (type[BaseModel] | None, optional): _description_. Defaults to None.
        circular_depency_strategy (CircularDepencyStrategy, optional): _description_. Defaults to "discard".

    Returns:
        type[BaseModel]: _description_
    """

    namespace = "sa_to_pydantic"

    created_models: dict[str, type[BaseModel]] = {}

    model_name = name_generator(model.__name__)

    if cache := REGISTRY.get_by_name(name=model_name):
        return cache.model

    _sa_to_pydantic(
        model=model,
        name_generator=name_generator,
        exclude_fields=exclude_fields,
        base_model=base_model,
        namespace=namespace,
        circular_depency_strategy=circular_depency_strategy,
        allow_optional=allow_optional,
    )

    if circular_depency_strategy == "forwardref":
        _types_namespace = REGISTRY.get(namespace)
        assert _types_namespace
        for m_name, m in created_models.items():
            m.model_rebuild(_types_namespace=_types_namespace)

    created_entry = REGISTRY.query_model(namespace=namespace, model_name=model_name)

    if not created_entry:
        print("REGISTRY......")
        print("-")
        print(f"{model=} {model_name=}")
        print("-")
        pprint(REGISTRY)
    assert (
        created_entry is not None
    ), f"Pydantic model not found in Registry for {model}"
    pydantic_model = created_entry.model

    # print("sa_to_pydantic :: created model ", model_name)
    # print(pydantic_model.model_fields)
    return pydantic_model


def make_type_optional(original_type: type[Any]) -> type[Any]:
    """Make a type optional by wrapping it in Union with NoneType.

    Args:
        original_type (type[Any]): The original type to be made optional.

    Returns:
        type[Any]: The modified type that is now optional.
    """
    origin = get_origin(original_type)
    args = get_args(original_type)

    if origin is Union or origin is UnionType:
        if type(None) in args:
            return original_type  # Already optional
        new_args = args + (type(None),)
        return Union[tuple(new_args)]  # type: ignore
    else:
        return Union[original_type, type(None)]  # type: ignore


def _sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
    _stack: set[str] | None = None,
    parent_model: type[DeclarativeBase] | None = None,
    namespace: str,
    created_models: dict[str, type[BaseModel]] = {},
    circular_depency_strategy: CircularDepencyStrategy,
    allow_optional: Callable[[type[DeclarativeBase], str], bool] | None = None,
) -> type[BaseModel] | ForwardRef | None:
    model_name = name_generator(model.__name__)
    # print("_sa_to_pydantic ..", model)
    if base_model:
        assert issubclass(base_model, BaseModel), f"{base_model} not a BaseModel"

    _stack = _stack or set()

    if namespace in REGISTRY and model_name in REGISTRY[namespace]:
        cache = REGISTRY[namespace][model_name]
        # assert parent_model is cache.parent_sa_model
        # print("_sa_to_pydantic :: REUSE", model_name, "parent:", parent_model, "=>", cache.model)
        return cache.model

    if model_name in _stack:
        if circular_depency_strategy == "raise":
            raise ValueError(f"Circular Depency detected: {model_name}")
        if circular_depency_strategy == "forwardref":
            return ForwardRef(model_name)
        if circular_depency_strategy == "discard":
            # print("DISCARD", model_name, "::", _stack, "::", REGISTRY)
            return None

    _stack.add(model_name)

    mapper = sa.inspect(model)
    relationships = mapper.relationships
    name2annotation = get_type_hints(model)

    fields: dict[str, Any] = {}

    for name, annotation in name2annotation.items():

        if exclude_fields and name in exclude_fields:
            continue

        allow_optional_ = allow_optional and allow_optional(model, name)

        field_kwargs = {}
        if allow_optional_:
            field_kwargs["default"] = None

        is_relationship = name in relationships

        inside_mapped_type = get_args(annotation)[0]

        inside_mapped_type_origin = get_origin(inside_mapped_type)

        is_union_type: bool = inside_mapped_type_origin in (Union, UnionType)
        # extract primitive fields
        if not is_relationship:
            if is_union_type:
                union_childs = get_args(inside_mapped_type)
                is_optional = type(None) in union_childs
                if is_optional:
                    field_kwargs["default"] = None

            if allow_optional_:
                inside_mapped_type = make_type_optional(inside_mapped_type)

            fields[name] = (
                inside_mapped_type,
                Field(**field_kwargs),
            )
        else:
            # extract reference fields
            sa_rel_model = extract_most_inner_type(annotation)

            annotation_type = _sa_to_pydantic(
                model=sa_rel_model,
                name_generator=name_generator,
                exclude_fields=None,
                _stack=_stack,
                circular_depency_strategy=circular_depency_strategy,
                parent_model=model,
                created_models=created_models,
                namespace=f"{namespace}.{sa_rel_model.__name__.lower()}",
                allow_optional=allow_optional,
            )
            # circular dependency in field => skip
            if annotation_type is None:
                continue

            if is_union_type:
                union_childs = get_args(inside_mapped_type)
                union_childs_replaced_sa = [
                    annotation_type if typ is sa_rel_model else typ
                    for typ in union_childs
                ]
                union_type = Union[tuple(union_childs_replaced_sa)]
                is_optional = type(None) in union_childs
                if is_optional:
                    field_kwargs["default"] = None
                fields[name] = (
                    union_type,
                    Field(**field_kwargs),
                )
            elif inside_mapped_type_origin is list:  # list ref field
                fields[name] = (list[annotation_type], Field(**field_kwargs))
            elif inside_mapped_type_origin is None:  # singular ref field
                fields[name] = (annotation_type, Field(**field_kwargs))
            else:
                raise ValueError(
                    f"Unresolved type inside Mapped {inside_mapped_type=} {inside_mapped_type_origin=}"
                )

    NewModel: type[BaseModel] = create_model(
        model_name,
        **fields,
        __base__=base_model or BaseModel,
        __config__={"from_attributes": True},
        __module__=namespace,
    )

    registry_entry = PydanticRegistryEntry(
        model=NewModel,
        sa_model=model,
        parent_sa_model=parent_model,
        name=model_name,
        namespace=namespace,
    )
    # print("NEW PydanticRegistryEntry....")
    # pprint(registry_entry)

    REGISTRY[namespace][model_name] = registry_entry

    created_models[name] = NewModel

    assert namespace in REGISTRY
    assert model_name in REGISTRY[namespace]

    # remove built model from stack
    _stack.remove(model_name)

    return NewModel
