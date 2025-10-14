from collections import defaultdict
from pydantic import BaseModel, Field, create_model
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from pprint import pprint
from typing import Any, ForwardRef, Literal, get_type_hints, get_origin, get_args, Callable
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
 
# Registry mapping model name to list of PydanticRegistryEntrys
# to handle multiple Pydantic models for the same SA model (e.g. different views)
class SaPydanticRegistryNameSpace(
    defaultdict[type[DeclarativeBase], list[PydanticRegistryEntry]]
):
    def __init__(self):
        super().__init__(list)  # list is the default factory

    def query_model(self, 
                    sa_model: type[DeclarativeBase],
                    query_fun: Callable[[PydanticRegistryEntry], bool],
                    ) -> PydanticRegistryEntry | None:    
        values = self.get(sa_model, [])
        matches = [entry for entry in values if query_fun(entry)]
        assert len(matches) == 0 or len(matches) == 1  
        return matches[0] if matches else None
    
REGISTRY = SaPydanticRegistryNameSpace()

def sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None,
    circular_depency_strategy: CircularDepencyStrategy = "discard"
) -> type[BaseModel]:
    
    reg_before = set(REGISTRY.keys())

    _sa_to_pydantic(
        model=model,
        name_generator=name_generator,
        exclude_fields=exclude_fields,
        base_model=base_model,
        circular_depency_strategy=circular_depency_strategy
    ) 

    if circular_depency_strategy == "forwardref":
        reg_after = set(REGISTRY.keys()) 
        reg_difference = reg_after - reg_before 
        newly_added_models = {
            k: REGISTRY[k] for k in reg_difference
        }

        for created_models in list(newly_added_models.values()):
            for created_model in created_models:
                created_model.model_rebuild(_types_namespace=REGISTRY)

    model_name = name_generator(model.__name__)

    resolved_result_model = REGISTRY.query_model(
        sa_model=model,
        query_fun=lambda x: x.name == model_name and x.parent_sa_model is None
        )
    if not resolved_result_model:
        print("REGISTRY......")
        print("-")
        print(f"{model=} {model_name=}")
        print("-")
        pprint(REGISTRY)
    assert resolved_result_model is not None, f"Pydantic model not found in Registry for {model}"
    pydantic_model = resolved_result_model.model
    return pydantic_model
 
def _sa_to_pydantic(
    *,
    model: type[DeclarativeBase],
    name_generator: Callable[[str], str],
    exclude_fields: list[str] | None = None,
    base_model: type[BaseModel] | None = None, 
    _stack: set[str] | None = None,
    parent_model: type[DeclarativeBase] | None = None,
    circular_depency_strategy: CircularDepencyStrategy
) -> type[BaseModel] | ForwardRef | None:
    model_name = name_generator(model.__name__)
    # print("_sa_to_pydantic ..", model)
    if base_model:
        assert issubclass(base_model, BaseModel), f"{base_model} not a BaseModel"

    _stack = _stack or set()
    
    if model in REGISTRY:
        
        cache = REGISTRY.query_model(
            sa_model=model, 
            query_fun=lambda x: x.parent_sa_model is parent_model and x.name == model_name)
        if cache is not None:
            assert parent_model is cache.parent_sa_model
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

        is_relationship = name in relationships

        inside_mapped_type = get_args(annotation)[0]

        inside_mapped_type_origin = get_origin(inside_mapped_type)

        is_union_type: bool = inside_mapped_type_origin in (Union, UnionType)
        # extract primitive fields
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
            # extract reference fields
            sa_rel_model = extract_most_inner_type(annotation) 

            annotation_type = _sa_to_pydantic(
            model=sa_rel_model,
            name_generator=name_generator,
            exclude_fields=None,
            _stack=_stack,
            circular_depency_strategy=circular_depency_strategy,
            parent_model=model
            )
            # circular dependency in field => skip
            if annotation_type is None:
                continue

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
    REGISTRY[model].append(
        PydanticRegistryEntry(
            model=NewModel,
            sa_model=model,
            parent_sa_model=parent_model,
            name=model_name
    ))

    assert model in REGISTRY

    # remove built model from stack
    _stack.remove(model_name)

    return NewModel
 